##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.teaching_material import postpone_teaching_materials, TeachingMaterial, find_by_learning_unit_year
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory


class TeachingMaterialTest(TestCase):
    def setUp(self):
        start_year = AcademicYearFactory(year=2015)
        end_year = AcademicYearFactory(year=2020)
        self.ac_years_containers = GenerateAcademicYear(start_year=start_year, end_year=end_year)
        self.learning_container = LearningContainerFactory()
        self.learning_unit = LearningUnitFactory(learning_container=self.learning_container)
        self.luys = {}
        for ac_year in self.ac_years_containers.academic_years:
            self.luys[ac_year] = LearningUnitYearFactory(
                acronym="LBIR1200",
                learning_unit=self.learning_unit,
                academic_year=ac_year,
                learning_container_year__learning_container=self.learning_container,
                learning_container_year__academic_year=ac_year
            )

    def test_postpone_teaching_materials(self):
        # Create multiple teaching material in 2015
        NB_TO_CREATE = 10
        ac_year_2015 = self.ac_years_containers.academic_years[0]
        start_luy = self.luys[ac_year_2015]
        for i in range(0, NB_TO_CREATE):
            TeachingMaterialFactory(learning_unit_year=start_luy)
        # Make postponement
        postpone_teaching_materials(start_luy)
        # Check if the teaching material has been postponed in future
        for ac_year in self.ac_years_containers.academic_years:
            self.assertEqual(TeachingMaterial.objects.filter(learning_unit_year__academic_year=ac_year).count(),
                             NB_TO_CREATE)

    def test_postpone_override_teaching_materials(self):
        """In this test, we ensure that postponement will override encoded in future"""
        luy_in_future = self.luys[self.ac_years_containers.academic_years[2]]  # Take ac year 2017
        teaching_material_in_future = TeachingMaterialFactory(learning_unit_year=luy_in_future)

        ac_year_2015 = self.ac_years_containers.academic_years[0]
        start_luy = self.luys[ac_year_2015]
        teaching_material_postponed = TeachingMaterialFactory(learning_unit_year=start_luy)
        # Make postponement
        postpone_teaching_materials(start_luy)
        # Ensure that teaching_material_in_future is deleted
        self.assertFalse(TeachingMaterial.objects.filter(pk=teaching_material_in_future.pk).exists())

        expected_result = [{'title': teaching_material_postponed.title,
                            'mandatory': teaching_material_postponed.mandatory,
                            'learning_unit_year_id': luy_in_future.id}]
        result = TeachingMaterial.objects.filter(learning_unit_year=luy_in_future)\
                                         .values('title', 'mandatory', 'learning_unit_year_id')
        self.assertListEqual(list(result), expected_result)

    def test_find_by_learning_unit_year(self):
        """This test will ensure that the order is determied by 'ORDER' field"""
        ac_year_2015 = self.ac_years_containers.academic_years[0]
        luy = self.luys[ac_year_2015]
        tm_1 = TeachingMaterialFactory(learning_unit_year=luy)
        tm_2 = TeachingMaterialFactory(learning_unit_year=luy)
        tm_3 = TeachingMaterialFactory(learning_unit_year=luy)

        result = find_by_learning_unit_year(luy)
        self.assertEqual(result.count(), 3)
        self.assertEqual(result[0], tm_1)
        self.assertEqual(result[1], tm_2)
        self.assertEqual(result[2], tm_3)

        # Set tm_1 to bottom and check result [Must use QS]
        TeachingMaterial.objects.get(pk=tm_1.pk).bottom()
        result = find_by_learning_unit_year(luy)
        self.assertEqual(result.count(), 3)
        self.assertEqual(result[0], tm_2)
        self.assertEqual(result[1], tm_3)
        self.assertEqual(result[2], tm_1)
