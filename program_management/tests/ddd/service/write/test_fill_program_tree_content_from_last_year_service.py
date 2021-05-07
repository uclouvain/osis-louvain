#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import namedtuple

import attr
import mock
from django.test import override_settings

from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.ddd.command import FillProgramTreeVersionContentFromProgramTreeVersionCommand, \
    FillProgramTreeContentFromLastYearCommand
from program_management.ddd.domain.exception import ProgramTreeNonEmpty, InvalidTreeVersionToFillTo
from program_management.ddd.domain.node import factory as node_factory
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.service.write import fill_program_tree_content_from_last_year_service
from program_management.ddd.service.write.fill_program_tree_version_content_from_program_tree_version_service import \
    fill_program_tree_version_content_from_program_tree_version
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.domain.program_tree.BACHELOR_1BA import ProgramTreeBachelorFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory, tree_builder
from program_management.tests.ddd.factories.program_tree_version import SpecificProgramTreeVersionFactory, \
    SpecificTransitionProgramTreeVersionFactory, StandardProgramTreeVersionFactory
from testing.testcases import DDDTestCase

PAST_ACADEMIC_YEAR_YEAR = 2020
CURRENT_ACADEMIC_YEAR_YEAR = 2021
NEXT_ACADEMIC_YEAR_YEAR = 2022


@override_settings(YEAR_LIMIT_EDG_MODIFICATION=PAST_ACADEMIC_YEAR_YEAR)
class TestFillProgramTreeContentFromLastYear(DDDTestCase):
    def setUp(self) -> None:
        self._init_fake_repos()

        tree_data = {
            "node_type": GroupType.COMMON_CORE,
            "year": CURRENT_ACADEMIC_YEAR_YEAR,
            "end_year": NEXT_ACADEMIC_YEAR_YEAR,
            "node_id": 21,
            "children": [
                {
                    "node_type": GroupType.SUB_GROUP,
                    "year": CURRENT_ACADEMIC_YEAR_YEAR,
                    "end_year": NEXT_ACADEMIC_YEAR_YEAR,
                    "node_id": 31,
                    "children": [
                        {
                            "node_type": NodeType.LEARNING_UNIT,
                            "year": CURRENT_ACADEMIC_YEAR_YEAR,
                            "end_date": NEXT_ACADEMIC_YEAR_YEAR,
                            "node_id": 41,
                        },
                        {
                            "node_type": NodeType.LEARNING_UNIT,
                            "year": CURRENT_ACADEMIC_YEAR_YEAR,
                            "end_date": NEXT_ACADEMIC_YEAR_YEAR,
                            "node_id": 42,
                        }
                    ]
                }
            ]
        }

        self.tree_from = tree_builder(tree_data)

        self.tree_to_fill = ProgramTreeFactory(
            root_node__code=self.tree_from.root_node.code,
            root_node__title=self.tree_from.root_node.title,
            root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            root_node__transition_name=NOT_A_TRANSITION,
            root_node__node_type=self.tree_from.root_node.node_type,
        )

        self.cmd = self._generate_cmd(self.tree_to_fill)

        self.add_tree_to_repo(self.tree_from)
        self.add_tree_to_repo(self.tree_to_fill)

        self.create_node_next_years()
        self.mock_copy_group()
        self.mock_copy_cms()

    def create_node_next_years(self):
        nodes = self.tree_from.root_node.get_all_children_as_nodes()
        for node in nodes:
            if node.is_group():
                continue
            next_year_node = node_factory.copy_to_next_year(node)
            self.add_node_to_repo(next_year_node)

    def mock_copy_cms(self):
        patcher = mock.patch(
            "program_management.ddd.domain.service.copy_tree_cms.CopyCms.from_tree",
            side_effect=lambda *args, **kwargs: None
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def mock_copy_group(self):
        patcher = mock.patch(
            "education_group.ddd.service.write.copy_group_service.copy_group",
            side_effect=lambda node: self.add_node_to_repo(node_factory.copy_to_next_year(node))
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_work_with_group(self):
        result = fill_program_tree_content_from_last_year_service.fill_program_tree_content_from_last_year(self.cmd)

        self.assertTrue(result)

    def test_should_persist(self):
        fill_program_tree_content_from_last_year_service.fill_program_tree_content_from_last_year(self.cmd)

        expected = [
            attr.evolve(child_node.entity_id, year=NEXT_ACADEMIC_YEAR_YEAR)
            for child_node in self.tree_from.root_node.get_all_children_as_nodes()
        ]
        actual = [
            child_node.entity_id
            for child_node in self.tree_to_fill.root_node.get_all_children_as_nodes()
        ]
        self.assertCountEqual(expected, actual)

    def _generate_cmd(
            self,
            tree_to: 'ProgramTree'
    ) -> 'FillProgramTreeContentFromLastYearCommand':
        return FillProgramTreeContentFromLastYearCommand(
            to_year=tree_to.entity_id.year,
            to_code=tree_to.entity_id.code
        )
