# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.test import TestCase

from base.models import validation_rule
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.validation_rule import ValidationRuleFactory
from program_management.ddd.domain.service.validation_rule import FieldValidationRule


class TestGetValidationRuleForField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_type = TrainingType.BACHELOR
        field_reference = 'TrainingForm.{type}.field'.format(type=cls.education_group_type.name)
        cls.rule = ValidationRuleFactory(
            field_reference=field_reference,
            initial_value='initial'
        )

    def test_should_raise_object_does_not_exist_when_no_matching_validation_rule(self):
        with self.assertRaises(validation_rule.ValidationRule.DoesNotExist):
            FieldValidationRule.get(self.education_group_type, "another_field")

    def test_should_return_validation_rule_when_matching_rule_exists(self):
        result = FieldValidationRule.get(self.education_group_type, "field")

        self.assertEqual(self.rule, result)
