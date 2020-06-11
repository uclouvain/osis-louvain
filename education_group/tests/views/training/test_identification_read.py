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

from base.models.enums.education_group_types import TrainingType
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from education_group.ddd.domain.training import Training
from program_management.ddd.domain.node import NodeGroupYear
from program_management.forms.custom_xls import CustomXlsForm
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestTrainingReadIdentification(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')
        cls.training_version = EducationGroupVersionFactory(
            offer__acronym="DROI2M",
            offer__partial_acronym="LDROI200M",
            offer__academic_year__year=2019,
            offer__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            root_group__acronym="DROI2M",
            root_group__partial_acronym="LDROI200M",
            root_group__academic_year__year=2019,
            root_group__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
        )
        ElementGroupYearFactory(group_year=cls.training_version.root_group)
        cls.url = reverse('training_identification', kwargs={'year': 2019, 'code': 'LDROI200M'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

        self.perm_patcher = mock.patch(
            "education_group.views.training.common_read."
            "TrainingRead._is_general_info_and_condition_admission_in_display_range",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_case_user_have_not_permission(self):
        self.client.force_login(UserFactory())
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_training_not_exists(self):
        dummy_url = reverse('training_identification', kwargs={'year': 2018, 'code': 'DUMMY100B'})
        response = self.client.get(dummy_url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group_app/training/identification_read.html")

    def test_assert_context_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['group_year'], self.training_version.root_group)
        self.assertEqual(response.context['education_group_version'], self.training_version)

        self.assertIsInstance(response.context['education_group_year'], Training)
        self.assertIsInstance(response.context['form_xls_custom'], CustomXlsForm)
        self.assertIsInstance(response.context['tree'], str)
        self.assertIsInstance(response.context['node'], NodeGroupYear)
        self.assertIsInstance(response.context['history'], QuerySet)
        self.assertIn('current_version', response.context)
        self.assertIn('academic_year_choices', response.context)
        self.assertIn('versions_choices', response.context)

    def test_assert_academic_year_choices_on_context_data(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.context['academic_year_choices'],
            [
                (self.url + "?path=" + str(self.training_version.root_group.element.pk), 2019)
            ]
        )

    def test_assert_active_tabs_is_identification_and_others_are_not_active(self):
        from education_group.views.training.common_read import Tab

        response = self.client.get(self.url)

        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.DIPLOMAS_CERTIFICATES]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.ADMINISTRATIVE_DATA]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.CONTENT]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.UTILIZATION]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['active'])
        self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['active'])

    def test_assert_displayed_general_information_tabs(self):
        from education_group.views.training.common_read import Tab

        with mock.patch(
                'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
                {self.training_version.root_group.education_group_type.name: {}}
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])

        with mock.patch(
                'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
                {}
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.GENERAL_INFO]['display'])

    def test_assert_displayed_skill_and_achievements_tabs(self):
        from education_group.views.training.common_read import Tab

        with mock.patch(
                'base.models.enums.education_group_types.TrainingType.with_skills_achievements',
                side_effect=(lambda: [self.training_version.root_group.education_group_type.name])
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])

        with mock.patch(
                'base.models.enums.education_group_types.TrainingType.with_skills_achievements',
                side_effect=(lambda: [])
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.SKILLS_ACHIEVEMENTS]['display'])

    def test_assert_displayed_admission_condition_tabs(self):
        from education_group.views.training.common_read import Tab

        with mock.patch(
                'base.models.enums.education_group_types.TrainingType.with_admission_condition',
                side_effect=(lambda: [self.training_version.root_group.education_group_type.name])
        ):
            response = self.client.get(self.url)
            self.assertTrue(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])

        with mock.patch(
                'base.models.enums.education_group_types.TrainingType.with_admission_condition',
                side_effect=(lambda: [])
        ):
            response = self.client.get(self.url)
            self.assertFalse(response.context['tab_urls'][Tab.ADMISSION_CONDITION]['display'])
