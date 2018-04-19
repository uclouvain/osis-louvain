##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import IntegrityError

from base.models import learning_achievements
from base.tests.factories.academic_year import create_current_academic_year
from reference.tests.factories.language import LanguageFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.learning_achievements import LearningAchievementsFactory


A_CODE_NAME = 'AA 1'
A2_CODE_NAME = 'AA 2'


class LearningAchievementsTest(TestCase):

    def setUp(self):
        current_academic_year = create_current_academic_year()
        generated_container = GenerateContainer(start_year=current_academic_year.year,
                                                end_year=current_academic_year.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        self.luy = generated_container_first_year.learning_unit_year_full
        self.language_fr = LanguageFactory(code='FR')
        self.language_en = LanguageFactory(code='EN')

    def test_unique(self):
        LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy, language=self.language_fr)
        with self.assertRaises(IntegrityError):
            LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy, language=self.language_fr)

    def test_find_by_learning_unit_year(self):
        luy_achievement_fr = LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                         language=self.language_fr)
        luy_achievement_en = LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                         language=self.language_en)
        result = learning_achievements.find_by_learning_unit_year(self.luy)
        self.assertIn(luy_achievement_fr, result)
        self.assertIn(luy_achievement_en, result)

    def test_find_by_learning_unit_year_order(self):
        luy_achievement_fr_1 = LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                           language=self.language_fr)
        luy_achievement_en_1 = LearningAchievementsFactory(code_name=A_CODE_NAME, learning_unit_year=self.luy,
                                                           language=self.language_en)
        luy_achievement_fr_2 = LearningAchievementsFactory(code_name=A2_CODE_NAME, learning_unit_year=self.luy,
                                                           language=self.language_fr)
        # By default, OrderModel insert with the highest model + 1
        expected_result = [luy_achievement_en_1, luy_achievement_fr_1, luy_achievement_fr_2]
        result = list(learning_achievements.find_by_learning_unit_year(self.luy))
        self.assertListEqual(result, expected_result)
