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
from django.test import TestCase

from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from learning_unit.ddd.repository.load_teaching_material import load_teaching_materials


class TestLoadTeachingMaterial(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.l_unit_1 = LearningUnitYearFactory()
        cls.teaching_material = [TeachingMaterialFactory(title="Title {}".format(idx),
                                                         learning_unit_year=cls.l_unit_1) for idx in range(5)]

    def test_load_teaching_materials(self):
        results = load_teaching_materials(self.l_unit_1.acronym, self.l_unit_1.academic_year.year)
        self.assertEqual(len(results), 5)
