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
import mock
from django.test import TestCase

from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.domain.service.generate_node_code import GenerateNodeCode
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestGenerateCodeFromParentNode(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_should_return_empty_string_when_parent_has_no_code(self):
        parent_node = NodeGroupYearFactory(code="")
        child_node_type = TrainingType.BACHELOR
        result = GenerateNodeCode.generate_from_parent_node(parent_node, child_node_type)
        self.assertEqual("", result)

    @mock.patch("program_management.ddd.domain.service.validation_rule.FieldValidationRule.get")
    def test_should_return_new_code_when_parent_has_a_code(self, mock_get_rule):
        mock_get_rule.return_value = mock.Mock()
        mock_get_rule.return_value.initial_value = '200E'

        parent_node = NodeGroupYearFactory(code="LDROI100B")
        child_node_type = MiniTrainingType.DEEPENING

        result = GenerateNodeCode.generate_from_parent_node(parent_node, child_node_type)
        self.assertEqual("LDROI200E", result)

    @mock.patch("program_management.ddd.domain.service.validation_rule.FieldValidationRule.get")
    def test_should_increment_cnum_number_when_generated_code_already_exists(self, mock_get_rule):
        mock_get_rule.return_value = mock.Mock()
        mock_get_rule.return_value.initial_value = '200E'

        group_year_with_generated_code = GroupYearFactory(partial_acronym="LDROI200E")
        parent_node = NodeGroupYearFactory(code="LDROI100B")
        child_node_type = MiniTrainingType.DEEPENING

        result = GenerateNodeCode.generate_from_parent_node(parent_node, child_node_type)
        self.assertEqual("LDROI201E", result)
