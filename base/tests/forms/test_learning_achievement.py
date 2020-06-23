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
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.forms.learning_achievement import LearningAchievementEditForm
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory, EnglishLanguageFactory


class TestLearningAchievementForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language_fr = FrenchLanguageFactory()
        cls.language_en = EnglishLanguageFactory()
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=create_current_academic_year()
        )
        cls.learning_achievement = LearningAchievementFactory(
            learning_unit_year=cls.learning_unit_year,
            language=cls.language_fr,
            code_name='TEST',
        )

    def test_should_not_raise_validation_error_case_update_same_achievement(self):
        text = 'text_edited'
        data = {
            'code_name': self.learning_achievement.code_name,
            'postpone': 0,
            'text_fr': text,
        }
        form = LearningAchievementEditForm(
            luy=self.learning_unit_year,
            data=data,
            code=self.learning_achievement.code_name,
            consistency_id=self.learning_achievement.consistency_id
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(self.learning_achievement.text, text)

    def test_should_raise_validation_error_case_existing_code(self):
        data = {
            'code_name': self.learning_achievement.code_name,
            'postpone': 0,
        }
        form = LearningAchievementEditForm(
            luy=self.learning_unit_year,
            data=data,
            consistency_id=2
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertDictEqual(
            form.errors,
            {
                'code_name': [
                    _("This code already exists for this learning unit")
                ],
            }
        )
