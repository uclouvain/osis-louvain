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

from django.contrib.auth.models import Permission
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from base.forms.learning_unit_pedagogy import TeachingMaterialModelForm
from base.models.enums.learning_unit_year_subtypes import FULL
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import CentralManagerFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory


class TeachingMaterialCreateTestCase(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            subtype=FULL,
            academic_year=self.current_academic_year,
            learning_container_year__academic_year=self.current_academic_year
        )
        self.url = reverse('teaching_material_create', kwargs={'learning_unit_year_id': self.learning_unit_year.id})
        self.person = _get_central_manager_person_with_permission()
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


class TeachingMaterialUpdateTestCase(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            subtype=FULL,
            academic_year=self.current_academic_year,
            learning_container_year__academic_year=self.current_academic_year
        )
        self.teaching_material = TeachingMaterialFactory(learning_unit_year=self.learning_unit_year)
        self.url = reverse('teaching_material_edit', kwargs={
                               'learning_unit_year_id': self.learning_unit_year.id,
                               'teaching_material_id': self.teaching_material.id
                           })
        self.person = _get_central_manager_person_with_permission()
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


class TeachingMaterialDeleteTestCase(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            subtype=FULL,
            academic_year=self.current_academic_year,
            learning_container_year__academic_year=self.current_academic_year
        )
        self.teaching_material = TeachingMaterialFactory(learning_unit_year=self.learning_unit_year)
        self.url = reverse('teaching_material_delete', kwargs={
            'learning_unit_year_id': self.learning_unit_year.id,
            'teaching_material_id': self.teaching_material.id
        })
        self.person = _get_central_manager_person_with_permission()
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


def _get_central_manager_person_with_permission():
    perm_codename = "can_edit_learningunit_pedagogy"
    person = CentralManagerFactory()
    person.user.user_permissions.add(Permission.objects.get(codename=perm_codename))
    return person
