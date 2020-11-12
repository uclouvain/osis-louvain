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
from typing import List
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import MiniTrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from base.utils.urls import reverse_with_get
from education_group.ddd.domain.group import Group
from education_group.views.mini_training.common_read import Tab
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestMiniTrainingReadSkillAchievementsRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.mini_training_version = StandardEducationGroupVersionFactory(
            offer__acronym="APPBIOL",
            offer__academic_year=cls.academic_year,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__partial_acronym="LBIOL100P",
            root_group__acronym="APPBIOL",
            root_group__academic_year=cls.academic_year,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )
        cls.element_group_year = ElementGroupYearFactory(group_year=cls.mini_training_version.root_group)

        cls.url = reverse(
            'mini_training_skills_achievements', kwargs={'year': cls.academic_year.year, 'code': 'LBIOL100P'}
        ) + '?path={}&tab={}'.format(cls.element_group_year.id, Tab.SKILLS_ACHIEVEMENTS)

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

        self.perm_patcher = mock.patch(
            "education_group.views.mini_training.skills_achievements_read.MiniTrainingReadSkillsAchievements."
            "have_skills_and_achievements_tab",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertTrue(
            '/login/?next=/educationgroups/mini_trainings/{}/LBIOL100P/skills_achievements/'.format(
                self.academic_year.year
            )
            in response.url
        )

    def test_case_user_have_not_permission(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_mini_training_unauthorized_skills_achievements_tab(self):
        with mock.patch(
            "education_group.views.mini_training.skills_achievements_read.MiniTrainingReadSkillsAchievements."
            "have_skills_and_achievements_tab",
            return_value=False
        ):
            response = self.client.get(self.url)
            expected_redirect = reverse('mini_training_identification', kwargs={
                'year': self.academic_year.year, 'code': 'LBIOL100P'
            })
            self.assertRedirects(response, expected_redirect)

    def test_case_mini_training_not_exists(self):
        dummy_url = reverse('mini_training_skills_achievements', kwargs={
            'year': self.academic_year.year, 'code': 'DUMMY100B'
        })
        response = self.client.get(dummy_url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group_app/mini_training/skills_achievements_read.html")

    def test_assert_context_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['group_year'], self.mini_training_version.root_group)
        self.assertEqual(response.context['education_group_version'], self.mini_training_version)
        expected_tree_json_url = reverse_with_get(
            'tree_json',
            kwargs={'root_id': self.mini_training_version.root_group.element.pk},
            get={"path": str(self.mini_training_version.root_group.element.pk)}
        )
        self.assertEqual(response.context['tree_json_url'], expected_tree_json_url)
        self.assertIsInstance(response.context['group'], Group)
        self.assertIsInstance(response.context['achievements'], List)
        self.assertIn("can_edit_information", response.context)

    def test_assert_label_structure_on_context_data(self):
        response = self.client.get(self.url)

        self.assertIsInstance(response.context['program_aims_label'], dict)
        self.assertIn("label_id", response.context['program_aims_label'])
        self.assertIn("text_fr", response.context['program_aims_label'])
        self.assertIn("text_en", response.context['program_aims_label'])

        self.assertIsInstance(response.context['additional_information_skills_label'], dict)
        self.assertIn("label_id", response.context['additional_information_skills_label'])
        self.assertIn("text_fr", response.context['additional_information_skills_label'])
        self.assertIn("text_en", response.context['additional_information_skills_label'])

    def test_assert_active_tabs_is_skills_achievements_and_others_are_not_active(self):
        response = self.client.get(self.url)

        self.assertTrue(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.CONTENT]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.UTILIZATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['active'])
