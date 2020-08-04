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
from django.test import SimpleTestCase

from base.models.enums.education_group_types import MiniTrainingType
from program_management.ddd.domain.service.generate_node_abbreviated_title import GenerateNodeAbbreviatedTitle
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestGenerateFromParentNode(SimpleTestCase):
    @mock.patch("program_management.ddd.domain.service.validation_rule.FieldValidationRule.get")
    def test_should_generate_title_by_concatening_child_type_default_value_with_parent_title(
            self,
            mock_get_field):
        mock_get_field.return_value.initial_value = "Initial Value"

        parent_node = NodeGroupYearFactory(title="Title")
        child_type = MiniTrainingType.DEEPENING
        result = GenerateNodeAbbreviatedTitle.generate(parent_node, child_type)

        self.assertEqual("INITIALVALUETitle", result)

