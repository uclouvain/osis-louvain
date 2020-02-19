##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import Permission
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from attribution.models.attribution import Attribution
from attribution.tests.factories.attribution import AttributionFactory
from base.tests.factories import structure
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.business.entities import create_entities_hierarchy
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.group import EntityManagerGroupFactory, ProgramManagerGroupFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory


class ScoresResponsibleSearchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = EntityManagerGroupFactory()
        group.permissions.add(Permission.objects.get(codename='view_scoresresponsible'))
        group.permissions.add(Permission.objects.get(codename='change_scoresresponsible'))

        cls.tutor = TutorFactory()
        cls.user = cls.tutor.person.user
        cls.academic_year = AcademicYearFactory(current=True)

        # FIXME: Old structure model [To remove]
        cls.structure = structure.StructureFactory()
        cls.structure_children = structure.StructureFactory(part_of=cls.structure)

        # New structure model
        entities_hierarchy = create_entities_hierarchy()
        cls.root_entity = entities_hierarchy.get('root_entity')
        cls.child_one_entity = entities_hierarchy.get('child_one_entity')
        cls.child_two_entity = entities_hierarchy.get('child_two_entity')
        cls.learning_unit_yr_req_entity_acronym = entities_hierarchy.get('child_one_entity_version').acronym
        cls.root_entity_acronym = entities_hierarchy.get('root_entity_version').acronym

        cls.entity_manager = EntityManagerFactory(
            person=cls.tutor.person,
            structure=cls.structure,
            entity=cls.root_entity,
        )

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            acronym="LBIR1210",
            structure=cls.structure,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1210",
            learning_container_year__requirement_entity=cls.child_one_entity,
        )

        cls.learning_unit_year_children = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            acronym="LBIR1211",
            structure=cls.structure_children,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1211",
            learning_container_year__requirement_entity=cls.child_two_entity,
        )

        cls.attribution = AttributionFactory(
            tutor=cls.tutor,
            learning_unit_year=cls.learning_unit_year,
            score_responsible=True
        )
        cls.attribution_children = AttributionFactory(
            tutor=cls.tutor,
            learning_unit_year=cls.learning_unit_year_children,
            score_responsible=True
        )
        cls.url = reverse('scores_responsible_list')
        cls.user.groups.add(group)

    def setUp(self):
        self.client.force_login(self.user)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'scores_responsible/list.html')

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_case_user_without_perms(self):
        unauthorized_user = UserFactory()
        self.client.force_login(unauthorized_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_case_search_without_filter_ensure_ordering(self):
        data = {
            'acronym': '',
            'learning_unit_title': '',
            'tutor': '',
            'scores_responsible': ''
        }
        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        qs_result = response.context['object_list']

        self.assertEqual(qs_result.count(), 2)
        self.assertEqual(qs_result[0], self.learning_unit_year)
        self.assertEqual(qs_result[1], self.learning_unit_year_children)

    def test_case_search_by_acronym_and_score_responsible(self):
        data = {
            'acronym': self.learning_unit_year.acronym,
            'learning_unit_title': '',
            'tutor': '',
            'scores_responsible': self.tutor.person.last_name
        }
        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        qs_result = response.context['object_list']

        self.assertEqual(qs_result.count(), 1)
        self.assertEqual(qs_result.first(), self.learning_unit_year)

    def test_case_ajax_return_json_response(self):
        data = {
            'acronym': self.learning_unit_year.acronym,
            'learning_unit_title': '',
            'tutor': '',
            'scores_responsible': self.tutor.person.last_name
        }
        response = self.client.get(self.url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, HttpResponse.status_code)

        expected_response = [
            {
                'pk': self.learning_unit_year.pk,
                'acronym': self.learning_unit_year.acronym,
                'requirement_entity': 'CHILD_1_V',
                'learning_unit_title': " - ".join([self.learning_unit_year.learning_container_year.common_title,
                                                   self.learning_unit_year.specific_title]),
                'attributions': [
                    {'tutor': str(self.attribution.tutor), 'score_responsible': self.attribution.score_responsible}
                ]
            }
        ]
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'object_list': expected_response}
        )

    def test_case_search_by_requirement_entity(self):
        data = self._data_search_by_req_entity()

        response = self.client.get(self.url, data=data)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        qs_result = response.context['object_list']

        self.assertEqual(qs_result.count(), 1)
        self.assertEqual(qs_result.first(), self.learning_unit_year)

    def test_case_search_by_requirement_entity_with_entity_subordinated(self):
        data = self._data_search_by_req_entity()
        data.update({'with_entity_subordinated': True})

        self._assert_equal_with_entity_subordinated(data, self.root_entity_acronym, [self.learning_unit_year,
                                                                                     self.learning_unit_year_children])
        self._assert_equal_with_entity_subordinated(data, self.learning_unit_yr_req_entity_acronym,
                                                    [self.learning_unit_year])

    def _assert_equal_with_entity_subordinated(self, data, entity, results):
        data.update({'requirement_entity': entity})

        response = self.client.get(self.url, data=data)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        qs_result = response.context['object_list']
        self.assertCountEqual(qs_result, results)

    def _data_search_by_req_entity(self):
        data = {
            'acronym': '',
            'learning_unit_title': '',
            'tutor': '',
            'scores_responsible': '',
            'requirement_entity': self.learning_unit_yr_req_entity_acronym
        }
        return data


class ScoresResponsibleManagementAsEntityManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = EntityManagerGroupFactory()
        group.permissions.add(Permission.objects.get(codename='view_scoresresponsible'))
        group.permissions.add(Permission.objects.get(codename='change_scoresresponsible'))

        cls.academic_year = AcademicYearFactory(year=datetime.date.today().year, start_date=datetime.date.today())

        # FIXME: Old structure model [To remove]
        cls.structure = structure.StructureFactory()

        entities_hierarchy = create_entities_hierarchy()
        cls.root_entity = entities_hierarchy.get('root_entity')

        cls.entity_manager = EntityManagerFactory(
            structure=cls.structure,
            entity=cls.root_entity,
        )
        cls.entity_manager.person.user.groups.add(group)

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            acronym="LBIR1210",
            structure=cls.structure,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1210",
            learning_container_year__requirement_entity=cls.root_entity,
        )

    def setUp(self):
        self.client.force_login(self.entity_manager.person.user)
        self.url = reverse('scores_responsible_management')
        self.get_data = {
            'learning_unit_year': "learning_unit_year_%d" % self.learning_unit_year.pk
        }

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_case_user_without_perms(self):
        unauthorized_user = UserFactory()
        self.client.force_login(unauthorized_user)

        response = self.client.get(self.url, data=self.get_data)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_case_user_which_cannot_managed_learning_unit_not_entity_managed(self):
        unauthorized_learning_unit_year = LearningUnitYearFactory()

        response = self.client.get(self.url, data={
            'learning_unit_year': "learning_unit_year_%d" % unauthorized_learning_unit_year.pk
        })
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url, data=self.get_data)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'scores_responsible_edit.html')


class ScoresResponsibleManagementAsProgramManagerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = ProgramManagerGroupFactory()
        group.permissions.add(Permission.objects.get(codename='view_scoresresponsible'))
        group.permissions.add(Permission.objects.get(codename='change_scoresresponsible'))

        cls.academic_year = create_current_academic_year()

        # FIXME: Old structure model [To remove]
        cls.structure = structure.StructureFactory()

        entities_hierarchy = create_entities_hierarchy()
        cls.root_entity = entities_hierarchy.get('root_entity')

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            acronym="LBIR1210",
            structure=cls.structure,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1210",
            learning_container_year__requirement_entity=cls.root_entity,
        )
        cls.education_group_year = EducationGroupYearFactory(
            academic_year=cls.academic_year,
            administration_entity=cls.root_entity
        )
        cls.program_manager = ProgramManagerFactory(education_group=cls.education_group_year.education_group)
        cls.program_manager.person.user.groups.add(group)
        offer_enrollment = OfferEnrollmentFactory(education_group_year=cls.education_group_year)
        LearningUnitEnrollmentFactory(offer_enrollment=offer_enrollment, learning_unit_year=cls.learning_unit_year)

    def setUp(self):
        self.client.force_login(self.program_manager.person.user)
        self.url = reverse('scores_responsible_management')
        self.get_data = {
            'learning_unit_year': "learning_unit_year_%d" % self.learning_unit_year.pk
        }

    def test_case_user_which_cannot_managed_learning_unit_not_entity_managed(self):
        unauthorized_learning_unit_year = LearningUnitYearFactory()

        response = self.client.get(self.url, data={
            'learning_unit_year': "learning_unit_year_%d" % unauthorized_learning_unit_year.pk
        })
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=2015)
    def test_assert_template_used(self):
        response = self.client.get(self.url, data=self.get_data)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'scores_responsible_edit.html')


class ScoresResponsibleAddTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = EntityManagerGroupFactory()
        group.permissions.add(Permission.objects.get(codename='view_scoresresponsible'))
        group.permissions.add(Permission.objects.get(codename='change_scoresresponsible'))

        cls.person = PersonFactory()
        cls.academic_year = AcademicYearFactory(year=datetime.date.today().year, start_date=datetime.date.today())

        # FIXME: Old structure model [To remove]
        cls.structure = structure.StructureFactory()

        entities_hierarchy = create_entities_hierarchy()
        cls.root_entity = entities_hierarchy.get('root_entity')

        cls.entity_manager = EntityManagerFactory(
            person=cls.person,
            structure=cls.structure,
            entity=cls.root_entity,
        )
        cls.entity_manager.person.user.groups.add(group)
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            acronym="LBIR1210",
            structure=cls.structure,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1210",
            learning_container_year__requirement_entity=cls.root_entity,
        )

    def setUp(self):
        attrib = AttributionFactory(learning_unit_year=self.learning_unit_year, score_responsible=False)
        self.url = reverse('scores_responsible_add', kwargs={'pk': self.learning_unit_year.pk})
        self.post_data = {
            'action': 'add',
            'attribution': "attribution_%d" % attrib.pk
        }
        self.client.force_login(self.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, data=self.post_data)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_case_user_without_perms(self):
        unauthorized_user = UserFactory()
        self.client.force_login(unauthorized_user)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_case_add_score_responsibles(self):
        response = self.client.post(self.url, data=self.post_data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

        self.assertTrue(
            Attribution.objects.filter(learning_unit_year=self.learning_unit_year, score_responsible=True).exists()
        )
