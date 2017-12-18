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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseForbidden

from base.tests.factories.academic_year import AcademicYearFakerFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.forms.learning_unit_proposal import LearningUnitProposalModificationForm
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.models.enums import organization_type, entity_type, entity_container_year_link_type, \
    learning_unit_year_subtypes, proposal_type, learning_container_year_types
from base.models import proposal_folder, proposal_learning_unit


class TestLearningUnitModificationProposal(TestCase):
    def setUp(self):
        today = datetime.date.today()

        self.person = PersonFactory()
        self.permission = Permission.objects.get(codename="can_propose_learningunit")
        self.person.user.user_permissions.add(self.permission)

        an_organization = OrganizationFactory(type=organization_type.MAIN)
        self.learning_unit_year = LearningUnitYearFakerFactory(acronym="LOSIS1212",
                                                               subtype=learning_unit_year_subtypes.FULL)
        self.learning_unit_year.academic_year.start_date = today - datetime.timedelta(days=15)
        self.learning_unit_year.academic_year.end_date = today + datetime.timedelta(days=15)
        self.learning_unit_year.academic_year.year = today.year
        self.learning_unit_year.academic_year.save()
        self.learning_unit_year.learning_container_year.container_type = learning_container_year_types.COURSE
        self.learning_unit_year.learning_container_year.save()
        self.learning_unit_year.learning_container_year.campus.organization = an_organization
        self.learning_unit_year.learning_container_year.campus.is_administration = True
        self.learning_unit_year.learning_container_year.campus.save()

        an_entity = EntityFactory(organization=an_organization)
        self.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL,
                                                   start_date=today - datetime.timedelta(days=25),
                                                   end_date=today.replace(year=today.year + 1))
        self.requirement_entity = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            entity=self.entity_version.entity,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )
        self.allocation_entity = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            entity=self.entity_version.entity,
            type=entity_container_year_link_type.ALLOCATION_ENTITY
        )
        self.additional_entity_1= EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            entity=self.entity_version.entity,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1
        )
        self.additional_entity_2 = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            entity=self.entity_version.entity,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2
        )

        self.person_entity = PersonEntityFactory(person=self.person, entity=an_entity, with_child=True)

        self.client.force_login(self.person.user)
        self.url = reverse('learning_unit_modification_proposal', args=[self.learning_unit_year.id])

        self.form_data = {
            "academic_year": self.learning_unit_year.academic_year.id,
            "first_letter": self.learning_unit_year.acronym[0],
            "acronym": self.learning_unit_year.acronym[1:],
            "title": self.learning_unit_year.title,
            "title_english": self.learning_unit_year.title_english,
            "container_type": self.learning_unit_year.learning_container_year.container_type,
            "internship_subtype": "",
            "credits": self.learning_unit_year.credits,
            "periodicity": self.learning_unit_year.learning_unit.periodicity,
            "status": self.learning_unit_year.status,
            "language": self.learning_unit_year.learning_container_year.language.id,
            "quadrimester": "",
            "campus": self.learning_unit_year.learning_container_year.campus.id,
            "requirement_entity": self.entity_version.id,
            "allocation_entity": self.entity_version.id,
            "additional_entity_1": self.entity_version.id,
            "additional_entity_2": self.entity_version.id,
            "folder_entity": self.entity_version.id,
            "folder_id": "1",
        }

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        self.person.user.user_permissions.remove(self.permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_with_non_existent_learning_unit_year(self):
        self.learning_unit_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_none_person(self):
        self.person.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['experimental_phase'], True)
        self.assertEqual(response.context['person'], self.person)

        self.assertIsInstance(response.context['form'], LearningUnitProposalModificationForm)
        form_initial = response.context['form'].initial
        self.assertEqual(form_initial['academic_year'], self.learning_unit_year.academic_year.pk)
        self.assertEqual(form_initial['first_letter'], self.learning_unit_year.acronym[0])
        self.assertEqual(form_initial['acronym'], self.learning_unit_year.acronym[1:])
        self.assertEqual(form_initial['title'], self.learning_unit_year.title)
        self.assertEqual(form_initial['container_type'], self.learning_unit_year.
                         learning_container_year.container_type)
        self.assertEqual(form_initial['subtype'], self.learning_unit_year.subtype)
        self.assertEqual(form_initial['credits'], self.learning_unit_year.credits)
        self.assertEqual(form_initial['periodicity'], self.learning_unit_year.learning_unit.periodicity)
        self.assertEqual(form_initial['status'], self.learning_unit_year.status)
        self.assertEqual(form_initial['language'], self.learning_unit_year.learning_container_year.language)
        self.assertEqual(form_initial['requirement_entity'], self.entity_version)
        self.assertEqual(form_initial['allocation_entity'], self.entity_version)
        self.assertEqual(form_initial['additional_entity_1'], self.entity_version)
        self.assertEqual(form_initial['additional_entity_2'], self.entity_version)
        self.assertEqual(form_initial['campus'], self.learning_unit_year.learning_container_year.campus)

    def test_post_request_with_invalid_form(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['experimental_phase'], True)
        self.assertEqual(response.context['person'], self.person)
        self.assertIsInstance(response.context['form'], LearningUnitProposalModificationForm)

    def test_post_request(self):
        response = self.client.post(self.url, data=self.form_data)

        redirected_url = reverse('learning_unit', args=[self.learning_unit_year.id])
        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)

        folder = proposal_folder.find_by_entity_and_folder_id(self.entity_version.entity, 1)
        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertTrue(folder)
        self.assertTrue(a_proposal_learning_unit)
        self.assertEqual(a_proposal_learning_unit.author, self.person)

        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn(_("success_modification_proposal").format(proposal_type.ProposalType.MODIFICATION.name,
                                                                self.learning_unit_year.acronym),
                      list(messages))

    def test_transformation_proposal_request(self):
        self.form_data["acronym"] = "OSIS1452"
        self.client.post(self.url, data=self.form_data)

        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertEqual(a_proposal_learning_unit.type, proposal_type.ProposalType.TRANSFORMATION.name)

    def test_modification_proposal_request(self):
        self.form_data["title"] = "New title"
        self.form_data["title_english"] = "New english title"
        self.client.post(self.url, data=self.form_data)

        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertEqual(a_proposal_learning_unit.type, proposal_type.ProposalType.MODIFICATION.name)

    def test_transformation_and_modification_proposal_request(self):
        self.form_data["acronym"] = "OSIS1452"
        self.form_data["title"] = "New title"
        self.form_data["title_english"] = "New english title"
        self.client.post(self.url, data=self.form_data)

        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertEqual(a_proposal_learning_unit.type, proposal_type.ProposalType.TRANSFORMATION_AND_MODIFICATION.name)

    def test_learning_unit_of_type_undefined(self):
        self.learning_unit_year.subtype = None
        self.learning_unit_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')

    def test_learning_unit_must_not_be_partim(self):
        self.learning_unit_year.subtype = learning_unit_year_subtypes.PARTIM
        self.learning_unit_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_learning_unit_of_type_internship(self):
        self.learning_unit_year.learning_container_year.container_type = learning_container_year_types.INTERNSHIP
        self.learning_unit_year.learning_container_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')

    def test_learning_unit_of_type_dissertation(self):
        self.learning_unit_year.learning_container_year.container_type = learning_container_year_types.DISSERTATION
        self.learning_unit_year.learning_container_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')

    def test_learning_unit_of_other_types(self):
        self.learning_unit_year.learning_container_year.container_type = learning_container_year_types.OTHER_COLLECTIVE
        self.learning_unit_year.learning_container_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_proposal_already_exists(self):
        ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_academic_year_inferior_to_current(self):
        today = datetime.date.today()
        self.learning_unit_year.academic_year = \
            AcademicYearFakerFactory(year=today.year-1, start_date=today.replace(day=1, year=today.year-1),
                                     end_date=today.replace(day=20, year=today.year-1))
        self.learning_unit_year.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_not_linked_to_entity(self):
        self.person_entity.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_not_linked_to_requirement_entity(self):
        today = datetime.date.today()
        an_entity = EntityFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        an_entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL,
                                                 start_date=today - datetime.timedelta(days=25),
                                                 end_date=today.replace(year=today.year + 1))

        self.requirement_entity.entity = an_entity_version.entity
        self.requirement_entity.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_linked_to_parent_entity(self):
        today = datetime.date.today()
        parent_entity = EntityFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        EntityVersionFactory(entity=parent_entity, entity_type=entity_type.SCHOOL,
                             start_date=today - datetime.timedelta(days=25),
                             end_date=today.replace(year=today.year + 1))

        self.entity_version.parent = parent_entity
        self.entity_version.save()

        self.person_entity.entity = parent_entity
        self.person_entity.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')

    def test_linked_to_child_entity(self):
        today = datetime.date.today()
        child_entity = EntityFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        EntityVersionFactory(entity=child_entity, entity_type=entity_type.SCHOOL,
                             start_date=today - datetime.timedelta(days=25),
                             end_date=today.replace(year=today.year + 1),
                             parent=self.entity_version.entity)

        self.person_entity.entity = child_entity
        self.person_entity.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

