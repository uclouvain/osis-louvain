##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import QuerySet
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import MiniTrainingType
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from education_group.views.mini_training.common_read import Tab
from program_management.ddd.domain.node import NodeGroupYear
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory, \
    ParticularTransitionEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestMiniTrainingReadIdentification(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.mini_training_version = StandardEducationGroupVersionFactory(
            offer__acronym="APPBIOL",
            offer__academic_year__year=2019,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__partial_acronym="LBIOL100P",
            root_group__academic_year__year=2019,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )
        cls.root_group_element = ElementGroupYearFactory(group_year=cls.mini_training_version.root_group)

        cls.url = reverse('mini_training_identification', kwargs={'year': 2019, 'code': 'LBIOL100P'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_case_user_have_not_permission(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_mini_training_not_exists(self):
        dummy_url = reverse('mini_training_identification', kwargs={'year': 2018, 'code': 'DUMMY100B'})
        response = self.client.get(dummy_url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group_app/mini_training/identification_read.html")

    def test_assert_context_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['group_year'], self.mini_training_version.root_group)
        self.assertEqual(response.context['education_group_version'], self.mini_training_version)
        self.assertIsInstance(response.context['tree'], str)
        self.assertIsInstance(response.context['node'], NodeGroupYear)
        self.assertIsInstance(response.context['history'], QuerySet)

    def test_assert_active_tabs_is_identification_and_others_are_not_active(self):
        response = self.client.get(self.url)

        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.CONTENT]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.UTILIZATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['active'])

    @mock.patch("education_group.views.mini_training.common_read."
                "MiniTrainingRead._is_general_info_and_condition_admission_in_display_range", return_value=True)
    def test_assert_displayed_general_information_tabs(self, mock_displayed_range):
        with mock.patch(
                'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
                {self.mini_training_version.root_group.education_group_type.name: {}}
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])

        with mock.patch(
            'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
            {}
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])

    @mock.patch("education_group.views.mini_training.common_read."
                "MiniTrainingRead._is_general_info_and_condition_admission_in_display_range", return_value=True)
    def test_assert_displayed_skill_and_achievements_tabs(self, mock_displayed_range):
        with mock.patch(
            'base.models.enums.education_group_types.MiniTrainingType.with_skills_achievements',
            side_effect=(lambda: [self.mini_training_version.root_group.education_group_type.name])
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])

        with mock.patch(
            'base.models.enums.education_group_types.MiniTrainingType.with_skills_achievements',
            side_effect=(lambda: [])
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])

    @mock.patch("education_group.views.mini_training.common_read."
                "MiniTrainingRead._is_general_info_and_condition_admission_in_display_range", return_value=True)
    def test_assert_displayed_admission_condition_tabs(self, mock_displayed_range):
        with mock.patch(
                'base.models.enums.education_group_types.MiniTrainingType.with_admission_condition',
                side_effect=(lambda: [self.mini_training_version.root_group.education_group_type.name])
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])

        with mock.patch(
                'base.models.enums.education_group_types.MiniTrainingType.with_admission_condition',
                side_effect=(lambda: [])
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])

    def test_assert_create_urls_correctly_computed(self):
        path = "{}".format(self.root_group_element.pk)
        expected_create_group_url = reverse('create_element_select_type', kwargs={'category': Categories.GROUP.name}) + \
            "?path_to={}".format(path)
        expected_create_training_url = reverse('create_element_select_type', kwargs={'category': Categories.TRAINING.name}) + \
            "?path_to={}".format(path)
        expected_create_mini_training_url = reverse('create_element_select_type',
                                                    kwargs={'category': Categories.MINI_TRAINING.name}) + \
            "?path_to={}".format(path)

        response = self.client.get(self.url)
        self.assertEqual(response.context['create_group_url'], expected_create_group_url)
        self.assertEqual(response.context['create_training_url'], expected_create_training_url)
        self.assertEqual(response.context['create_mini_training_url'], expected_create_mini_training_url)

    def test_assert_delete_url_correctly_computed(self):
        path = "{}".format(self.root_group_element.pk)
        expected_delete_mini_training_url = reverse('mini_training_delete', kwargs={'year': 2019, 'code': 'LBIOL100P'}) + \
            "?path={}".format(path)

        response = self.client.get(self.url)
        self.assertEqual(response.context['delete_mini_training_url'], expected_delete_mini_training_url)


class TestMiniTrainingReadIdentificationTabs(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.standard_mini_training_version = StandardEducationGroupVersionFactory(
            offer__academic_year__year=2019,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__partial_acronym="LBIOL100P",
            root_group__academic_year__year=2019,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )
        ElementGroupYearFactory(group_year=cls.standard_mini_training_version.root_group)

        cls.url_standard = reverse('mini_training_identification', kwargs={'year': 2019, 'code': 'LBIOL100P'})

        cls.non_standard_mini_training_version = ParticularTransitionEducationGroupVersionFactory(
            offer__academic_year__year=2019,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__partial_acronym="LDRT100P",
            root_group__academic_year__year=2019,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )
        ElementGroupYearFactory(group_year=cls.non_standard_mini_training_version.root_group)

        cls.url_non_particular = reverse('mini_training_identification', kwargs={'year': 2019, 'code': 'LDRT100P'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_assert_tabs_displayed_for_standard_version(self):
        response = self.client.get(self.url_standard)

        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.CONTENT]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.UTILIZATION]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])

    def test_assert_tabs_displayed_for_particular_version(self):
        response = self.client.get(self.url_non_particular)

        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.CONTENT]['display'])
        self.assertTrue(response.context['tab_urls'][Tab.UTILIZATION]['display'])
        self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])
        self.assertFalse(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])
        self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])
