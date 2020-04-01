############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
############################################################################
from unittest import mock

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearBachelorFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.views.education_groups.achievement.detail import CMS_LABEL_PROGRAM_AIM, CMS_LABEL_ADDITIONAL_INFORMATION
from base.views.education_groups.detail import EducationGroupGenericDetailView
from cms.enums import entity_name
from cms.tests.factories.translated_text import TranslatedTextFactory


class TestEducationGroupSkillsAchievements(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.perm_patcher = mock.patch(
            "base.business.education_groups.perms.AdmissionConditionPerms.is_eligible",
            return_value=True
        )

        cls.education_group_year = EducationGroupYearBachelorFactory(
            academic_year=AcademicYearFactory(current=True)
        )
        cls.person = PersonWithPermissionsFactory("can_access_education_group")

    def setUp(self):
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)
        self.client.force_login(self.person.user)

    def _call_url_as_http_get(self):
        response = self.client.get(
            reverse("education_group_skills_achievements",
                    args=[self.education_group_year.pk, self.education_group_year.pk])
        )
        self.assertEqual(response.status_code, HttpResponse.status_code)
        return response

    @mock.patch.object(EducationGroupGenericDetailView, "show_skills_and_achievements")
    def test_can_show_view_call_correct_function(self, mock_method):
        self._call_url_as_http_get()
        self.assertEqual(2, mock_method.call_count)

    def test_get_achievements(self):
        achievement = EducationGroupAchievementFactory(education_group_year=self.education_group_year)

        response = self._call_url_as_http_get()

        self.assertEqual(
            response.context["education_group_achievements"][0], achievement
        )

    def test_context_have_can_edit_information_args(self):
        response = self._call_url_as_http_get()
        self.assertTrue("can_edit_information" in response.context)
        self.assertTrue(response.context["can_edit_information"])

    def test_get_certificate_aim(self):
        certificate_aim_french = TranslatedTextFactory(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.id,
            text_label__label=CMS_LABEL_PROGRAM_AIM,
            language=settings.LANGUAGE_CODE_FR,
        )
        certificate_aim_english = TranslatedTextFactory(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.id,
            text_label__label=CMS_LABEL_PROGRAM_AIM,
            language=settings.LANGUAGE_CODE_EN,
        )
        response = self._call_url_as_http_get()
        self.assertEqual(
            response.context[CMS_LABEL_PROGRAM_AIM][settings.LANGUAGE_CODE_FR], certificate_aim_french
        )
        self.assertEqual(
            response.context[CMS_LABEL_PROGRAM_AIM][settings.LANGUAGE_CODE_EN], certificate_aim_english
        )

    def test_get_additional_informations(self):
        additional_infos_french = TranslatedTextFactory(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.id,
            text_label__label=CMS_LABEL_ADDITIONAL_INFORMATION,
            language=settings.LANGUAGE_CODE_FR,
        )
        additional_infos_english = TranslatedTextFactory(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.id,
            text_label__label=CMS_LABEL_ADDITIONAL_INFORMATION,
            language=settings.LANGUAGE_CODE_EN,
        )
        response = self._call_url_as_http_get()
        self.assertEqual(
            response.context[CMS_LABEL_ADDITIONAL_INFORMATION][settings.LANGUAGE_CODE_FR],
            additional_infos_french
        )
        self.assertEqual(
            response.context[CMS_LABEL_ADDITIONAL_INFORMATION][settings.LANGUAGE_CODE_EN],
            additional_infos_english
        )
