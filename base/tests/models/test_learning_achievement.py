##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from django.db import IntegrityError
from django.test import TestCase

from base.models import learning_achievement
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.learning_achievement import LearningAchievementFactory
from reference.tests.factories.language import LanguageFactory, EnglishLanguageFactory, FrenchLanguageFactory

A_CODE_NAME = 'AA 1'
A2_CODE_NAME = 'AA 2'


class LearningAchievementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_academic_year = create_current_academic_year()
        generated_container = GenerateContainer(start_year=current_academic_year, end_year=current_academic_year)
        generated_container_first_year = generated_container.generated_container_years[0]
        cls.luy = generated_container_first_year.learning_unit_year_full
        cls.language_fr = FrenchLanguageFactory()
        cls.language_en = EnglishLanguageFactory()

    def test_unique(self):
        LearningAchievementFactory(consistency_id=1, learning_unit_year=self.luy, language=self.language_fr)
        with self.assertRaises(IntegrityError):
            LearningAchievementFactory(consistency_id=1, learning_unit_year=self.luy, language=self.language_fr)

    def test_find_by_learning_unit_year(self):
        luy_achievement_fr = LearningAchievementFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                        language=self.language_fr)
        luy_achievement_en = LearningAchievementFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                        language=self.language_en)
        result = learning_achievement.find_by_learning_unit_year(self.luy)
        self.assertIn(luy_achievement_fr, result)
        self.assertIn(luy_achievement_en, result)

    def test_find_by_learning_unit_year_order(self):
        luy_achievement_fr_1 = LearningAchievementFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                          language=self.language_fr)
        luy_achievement_en_1 = LearningAchievementFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                          language=self.language_en)
        luy_achievement_fr_2 = LearningAchievementFactory(code_name=A2_CODE_NAME, learning_unit_year=self.luy,
                                                          language=self.language_fr)
        # By default, OrderModel insert with the highest model + 1
        expected_result = [luy_achievement_en_1, luy_achievement_fr_1, luy_achievement_fr_2]
        result = list(learning_achievement.find_by_learning_unit_year(self.luy))
        self.assertListEqual(result, expected_result)

    def test_find_learning_unit_achievement(self):
        luy_achievement_fr_1 = LearningAchievementFactory(code_name=A_CODE_NAME,
                                                          learning_unit_year=self.luy,
                                                          language=self.language_fr)
        self.assertEqual(learning_achievement.find_learning_unit_achievement(
            luy_achievement_fr_1.consistency_id,
            luy_achievement_fr_1.learning_unit_year,
            luy_achievement_fr_1.language.code,
            0
        ), luy_achievement_fr_1)
        self.assertIsNone(learning_achievement.find_learning_unit_achievement(
            luy_achievement_fr_1.consistency_id,
            luy_achievement_fr_1.learning_unit_year,
            luy_achievement_fr_1.language.code,
            100
        ))

    def test_find_previous_achievements_no_result(self):
        luy_achievement_fr = LearningAchievementFactory(code_name=A_CODE_NAME,
                                                        learning_unit_year=self.luy,
                                                        language=self.language_fr)
        self.assertCountEqual(learning_achievement.find_previous_achievements(luy_achievement_fr.learning_unit_year,
                                                                              luy_achievement_fr.language,
                                                                              luy_achievement_fr.order), [])
        self.assertCountEqual(learning_achievement.find_previous_achievements(None,
                                                                              luy_achievement_fr.language,
                                                                              luy_achievement_fr.order), [])

    def test_find_previous_achievements(self):
        luy_achievement_fr_0 = LearningAchievementFactory(code_name=A_CODE_NAME,
                                                          learning_unit_year=self.luy,
                                                          language=self.language_fr)
        luy_achievement_fr_1 = LearningAchievementFactory(code_name=A2_CODE_NAME,
                                                          learning_unit_year=self.luy,
                                                          language=self.language_fr)
        self.assertCountEqual(learning_achievement.find_previous_achievements(luy_achievement_fr_1.learning_unit_year,
                                                                              luy_achievement_fr_1.language,
                                                                              luy_achievement_fr_1.order),
                              [luy_achievement_fr_0])
