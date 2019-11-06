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

from base.tests.factories.learning_component_year import LearningComponentYearFactory
from learning_unit.api.serializers.component import LearningUnitComponentSerializer


class LearningUnitComponentSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.component = LearningComponentYearFactory()
        cls.serializer = LearningUnitComponentSerializer(cls.component)

    def test_contains_expected_fields(self):
        expected_fields = [
            'type',
            'type_text',
            'planned_classes',
            'hourly_volume_total_annual',
            'hourly_volume_total_annual_computed'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_compute_correct_volume(self):
        self.assertEqual(
            self.serializer.data['hourly_volume_total_annual_computed'],
            str(self.component.vol_global)
        )
