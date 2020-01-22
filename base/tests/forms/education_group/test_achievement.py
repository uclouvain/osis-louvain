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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from backoffice.settings.base import LANGUAGE_CODE_FR
from base.forms.education_group.achievement import EducationGroupAchievementCMSForm
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.views.test_my_osis import LANGUAGE_CODE_EN
from cms.tests.factories.text_label import TextLabelFactory


class TestInitEducationGroupAchievementCMSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        cls.cms_text_label = TextLabelFactory()

    def test_init_case_parms_not_rigth_instance(self):
        education_group = self.education_group_year.education_group
        with self.assertRaises(AttributeError):
            EducationGroupAchievementCMSForm(
                education_group_year=education_group,
                cms_text_label=self.cms_text_label
            )

        with self.assertRaises(AttributeError):
            EducationGroupAchievementCMSForm(
                education_group_year=self.education_group_year,
                cms_text_label=self.education_group_year
            )

    def test_init_without_mandatory_kwargs(self):
        with self.assertRaises(KeyError):
            EducationGroupAchievementCMSForm()

    def test_init_case_success(self):
        EducationGroupAchievementCMSForm(
            education_group_year=self.education_group_year,
            cms_text_label=self.cms_text_label
        )


class TestGetRelatedTextEducationGroupAchievementCMSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        cls.cms_text_label = TextLabelFactory()

    def test_get_related_text_in_french(self):
        expected_result = 'Text in french'
        form = EducationGroupAchievementCMSForm(
            education_group_year=self.education_group_year,
            cms_text_label=self.cms_text_label,
            data= {'text_french': expected_result, 'text_english': 'Text in english'}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form._get_related_text(LANGUAGE_CODE_FR), expected_result)

    def test_get_related_text_in_english(self):
        expected_result = 'Text in english'
        form = EducationGroupAchievementCMSForm(
            education_group_year=self.education_group_year,
            cms_text_label=self.cms_text_label,
            data={'text_french': 'Text in french', 'text_english': expected_result}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form._get_related_text(LANGUAGE_CODE_EN), expected_result)

    def test_get_related_text_case_not_supported_language(self):
        form = EducationGroupAchievementCMSForm(
            education_group_year=self.education_group_year,
            cms_text_label=self.cms_text_label,
            data={'text_french': 'Text in french', 'text_english': 'Text in english'}
        )
        self.assertTrue(form.is_valid())
        with self.assertRaises(AttributeError):
            self.assertEqual(form._get_related_text('DUMMY-LANGUAGE'))
