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

from base.tests.factories.teaching_material import TeachingMaterialFactory
from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
from learning_unit.ddd.repository.load_teaching_material import bulk_load_teaching_materials, \
    convert_teaching_material_db_row_to_domain_object


class TestBulkLoadTeachingMaterial(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teaching_materials = TeachingMaterialFactory.create_batch(2)

    def test_should_return_empty_dictionnary_when_no_identities_given(self):
        result = bulk_load_teaching_materials([])
        self.assertEqual(result, {})

    def test_should_return_a_mapping_of_identity_and_teaching_materials_when_identities_given(self):
        identities = [
            LearningUnitYearIdentity(
                code=material.learning_unit_year.acronym,
                year=material.learning_unit_year.academic_year.year
            )
            for material in self.teaching_materials
        ]
        result = bulk_load_teaching_materials(identities)
        expected_result = {
            identities[0]: [convert_teaching_material_db_row_to_domain_object(self.teaching_materials[0])],
            identities[1]: [convert_teaching_material_db_row_to_domain_object(self.teaching_materials[1])]
        }
        self.assertEqual(result, expected_result)
