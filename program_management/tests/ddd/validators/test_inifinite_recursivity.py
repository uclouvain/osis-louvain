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
import copy
from unittest.mock import patch

from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType, GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.domain.exception import CannotPasteNodeToHimselfException, CannotAttachParentNodeException
from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityTreeValidator, \
    InfiniteRecursivityLinkValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestInfiniteRecursivityTreeValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        """
        DROI1BA
         |---- COMMON_CORE
                |---- SUBGROUP

        WARNING : Int these unit tests, we're using mocks of repository instead of fake_repository
        WARNING : because we need 2 different results for repository.get() and repository.search_from_children()
        """
        self.academic_year = AcademicYearFactory.build(current=True)

        self.droi1ba = NodeGroupYearFactory(
            year=self.academic_year.year, title='DROI1BA', node_type=TrainingType.BACHELOR
        )
        self.common_core = NodeGroupYearFactory(
            year=self.academic_year.year, title='COMMON_CORE', node_type=GroupType.COMMON_CORE
        )
        self.subgroup = NodeGroupYearFactory(
            year=self.academic_year.year, title='SUBGROUP', node_type=GroupType.SUB_GROUP
        )
        self.droi1ba.add_child(self.common_core)
        self.common_core.add_child(self.subgroup)

        self.tree_droi1ba = ProgramTreeFactory(root_node=self.droi1ba)
        self.path_to_subgroup = build_path(self.droi1ba, self.common_core, self.subgroup)

        self._mock_trees_using_nodes()

    def _mock_trees_using_nodes(self):
        patcher = patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.search_from_children')
        self.addCleanup(patcher.stop)
        self.mock_trees_using_nodes = patcher.start()
        self.mock_trees_using_nodes.return_value = []

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_should_not_raise_eception_when_no_recursivity_found(self, mock_tree_of_node_to_paste):
        node_to_paste = NodeGroupYearFactory(
            year=self.academic_year.year, title="inexisting group in DROI1BA", node_type=GroupType.SUB_GROUP
        )

        mock_tree_of_node_to_paste.return_value = ProgramTreeFactory(root_node=node_to_paste)

        self.assertValidatorNotRaises(InfiniteRecursivityTreeValidator(
            self.tree_droi1ba,
            node_to_paste,
            self.path_to_subgroup,
            ProgramTreeRepository()
        ))

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_when_node_to_paste_is_learning_unit(self, mock_tree_of_node_to_paste):
        node_to_paste = NodeLearningUnitYearFactory(
            year=self.academic_year.year, title="inexisting in DROI1BA"
        )

        self.assertValidatorNotRaises(InfiniteRecursivityTreeValidator(
            self.tree_droi1ba,
            node_to_paste,
            self.path_to_subgroup,
            ProgramTreeRepository()
        ))

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_when_node_to_paste_is_parent_of_node_where_to_paste(self, mock_tree_of_node_to_paste):
        node_to_paste = self.droi1ba
        path_where_to_paste = self.path_to_subgroup

        mock_tree_of_node_to_paste.return_value = ProgramTreeFactory(root_node=node_to_paste)

        with self.assertRaises(CannotAttachParentNodeException):
            InfiniteRecursivityTreeValidator(
                self.tree_droi1ba,
                node_to_paste,
                path_where_to_paste,
                ProgramTreeRepository()
            ).validate()

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_when_node_to_paste_contains_child_that_is_parent_of_node_where_to_paste(self, mock_tree_of_node_to_paste):
        node_to_paste = NodeGroupYearFactory(
            year=self.academic_year.year,
        )  # node not used in DROI1BA ...
        node_to_paste.add_child(self.droi1ba)  # ... but the child is one of the parent of the common_Core.

        mock_tree_of_node_to_paste.return_value = ProgramTreeFactory(root_node=node_to_paste)
        where_to_paste = self.path_to_subgroup

        with self.assertRaises(CannotAttachParentNodeException):
            InfiniteRecursivityTreeValidator(
                self.tree_droi1ba,
                node_to_paste,
                where_to_paste,
                ProgramTreeRepository()
            ).validate()

    @patch('program_management.ddd.repositories.program_tree.ProgramTreeRepository.get')
    def test_when_node_to_paste_contains_child_that_is_parent_of_node_where_to_paste_in_another_tree(
            self,
            mock_tree_of_node_to_paste
    ):
        where_to_paste = self.subgroup
        path_where_to_paste = self.path_to_subgroup

        node_to_paste = NodeGroupYearFactory(
            year=self.academic_year.year,
        )
        child_of_node_to_paste = NodeGroupYearFactory(year=self.academic_year.year)
        node_to_paste.add_child(child_of_node_to_paste)
        mock_tree_of_node_to_paste.return_value = ProgramTreeFactory(root_node=node_to_paste)

        # another tree where the node to paste is reused AND where one of its parent is a child of node to paste
        another_tree_using_node = ProgramTreeFactory()
        another_tree_using_node.root_node.add_child(copy.deepcopy(child_of_node_to_paste))
        another_tree_using_node.root_node.children_as_nodes[0].add_child(where_to_paste)
        self.mock_trees_using_nodes.return_value = [
            another_tree_using_node
        ]

        with self.assertRaises(CannotAttachParentNodeException):
            InfiniteRecursivityTreeValidator(
                self.tree_droi1ba,
                node_to_paste,
                path_where_to_paste,
                ProgramTreeRepository()
            ).validate()


class TestInfiniteRecursivityLinkValidator(TestValidatorValidateMixin, SimpleTestCase):
    def setUp(self):
        self.tree = ProgramTreeFactory()

    def test_should_not_raise_exception_when_no_recursivity_found(self):
        node_to_attach = NodeGroupYearFactory()

        self.assertValidatorNotRaises(InfiniteRecursivityLinkValidator(self.tree.root_node, node_to_attach))

    def test_should_raise_exception_when_adding_node_to_himself(self):
        with self.assertRaises(CannotPasteNodeToHimselfException):
            InfiniteRecursivityLinkValidator(self.tree.root_node, self.tree.root_node).validate()
