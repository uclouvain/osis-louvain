##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.http import HttpResponseNotAllowed, HttpResponse
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from base.forms.learning_unit_pedagogy import TeachingMaterialModelForm
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.teaching_material import TeachingMaterial
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import CentralManagerForUEFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.utils.get_messages import get_messages_from_response


class TeachingMaterialCreateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year, *cls.future_academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        learning_unit = LearningUnitFactory()
        cls.learning_unit_year, *cls.future_learning_unit_years = [
            LearningUnitYearFactory(subtype=FULL, academic_year=acy, learning_unit=learning_unit)
            for acy in ([cls.current_academic_year] + cls.future_academic_years)
        ]
        cls.previous_luy = LearningUnitYearFactory(
            subtype=FULL,
            academic_year=AcademicYearFactory(year=cls.current_academic_year.year-1),
            learning_unit=learning_unit
        )
        cls.url = reverse('teaching_material_create', kwargs={'learning_unit_year_id': cls.learning_unit_year.id})
        cls.person = _get_central_manager_person_with_permission()

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_teaching_material_create_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_create_when_method_not_allowed(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_create_template_used(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'learning_unit/teaching_material/modal_edit.html')
        self.assertIsInstance(response.context['form'], TeachingMaterialModelForm)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    @mock.patch('base.views.learning_units.pedagogy.update.is_pedagogy_data_must_be_postponed')
    def test_create_teaching_material_successfull_post_without_postponement(
            self, mock_is_pedagogy_data_must_be_postponed, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        mock_is_pedagogy_data_must_be_postponed.return_value = False
        msg = self._test_teaching_material_post()
        self.assertEqual(msg[0].get('message'), "{}.".format(_("The learning unit has been updated")))
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_create_teaching_material_successfull_post_with_postponement(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        msg = self._test_teaching_material_post()
        expected_message = "{} {}.".format(
            _("The learning unit has been updated"),
            _("and postponed until %(year)s") % {
                "year": self.future_learning_unit_years[-1].academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_create_teaching_material_successfull_post_with_proposal_same_year(self,  mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        proposal = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)
        msg = self._test_teaching_material_post()
        expected_message = "{}. {}.".format(
            _("The learning unit has been updated"),
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_create_teaching_material_successfull_post_with_proposal_prev_year(self,  mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        ProposalLearningUnitFactory(learning_unit_year=self.previous_luy)
        msg = self._test_teaching_material_post()
        expected_message = "{}.".format(_("The learning unit has been updated"))
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_create_teaching_material_successfull_post_with_proposal_next_year(self,  mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        proposal = ProposalLearningUnitFactory(learning_unit_year=self.future_learning_unit_years[0])
        msg = self._test_teaching_material_post()
        expected_message = "{} ({}).".format(
            _("The learning unit has been updated"),
            _("the report has not been done from %(proposal_year)s because the LU is in proposal") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def _test_teaching_material_post(self):
        response = self.client.post(self.url, data={"mandatory": "True", "title": "This is a test"})
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue(
            TeachingMaterial.objects.get(
                mandatory=True,
                title="This is a test",
                learning_unit_year=self.learning_unit_year
            )
        )
        msg = get_messages_from_response(response)
        return msg


class TeachingMaterialUpdateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year, *cls.future_academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        cls.learning_unit_year, *cls.future_learning_unit_years = [
            LearningUnitYearFactory(subtype=FULL, academic_year=acy)
            for acy in ([cls.current_academic_year] + cls.future_academic_years)
        ]
        cls.person = _get_central_manager_person_with_permission()

    def setUp(self):
        self.teaching_material = TeachingMaterialFactory(learning_unit_year=self.learning_unit_year)
        self.url = reverse('teaching_material_edit', kwargs={
            'learning_unit_year_id': self.learning_unit_year.id,
            'teaching_material_id': self.teaching_material.id
        })
        self.client.force_login(self.person.user)

    def test_teaching_material_update_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_update_when_method_not_allowed(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_create_template_used(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'learning_unit/teaching_material/modal_edit.html')
        self.assertIsInstance(response.context['form'], TeachingMaterialModelForm)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_should_update_teaching_material_when_successfull_post(self,  mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.post(self.url, data={"mandatory": "True", "title": "This is a test"})

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue(
            TeachingMaterial.objects.get(mandatory=True, title="This is a test")
        )


class TeachingMaterialDeleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year, *cls.future_academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        cls.learning_unit_year, *cls.future_learning_unit_years = [
            LearningUnitYearFactory(subtype=FULL, academic_year=acy)
            for acy in ([cls.current_academic_year] + cls.future_academic_years)
        ]
        cls.person = _get_central_manager_person_with_permission()

    def setUp(self):
        self.teaching_material = TeachingMaterialFactory(learning_unit_year=self.learning_unit_year)
        self.url = reverse('teaching_material_delete', kwargs={
            'learning_unit_year_id': self.learning_unit_year.id,
            'teaching_material_id': self.teaching_material.id
        })
        self.client.force_login(self.person.user)

    def test_teaching_material_delete_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_update_when_method_not_allowed(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.options(self.url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_teaching_material_create_template_used(self, mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'learning_unit/teaching_material/modal_delete.html')

    @mock.patch('base.models.person.Person.is_linked_to_entity_in_charge_of_learning_unit_year')
    def test_should_delete_teaching_material_when_successfull_post(self,  mock_is_linked_to_entity_charge):
        mock_is_linked_to_entity_charge.return_value = True
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertFalse(
            TeachingMaterial.objects.filter(id=self.teaching_material.id).exists()
        )


def _get_central_manager_person_with_permission():
    perm_codename = "can_edit_learningunit_pedagogy"
    person = CentralManagerForUEFactory()
    person.user.user_permissions.add(Permission.objects.get(codename=perm_codename))
    return person
