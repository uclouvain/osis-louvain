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
from unittest import skip

import attr

from base.models.enums.education_group_types import GroupType
from base.models.enums.link_type import LinkTypes
from program_management.ddd import command
from program_management.ddd.domain.exception import CannotPasteToLearningUnitException, InvalidBlockException, \
    ReferenceLinkNotAllowedWithLearningUnitException, ChildTypeNotAuthorizedException, \
    ParentAndChildMustHaveSameAcademicYearException, MaximumChildTypesReachedException, \
    CannotPasteNodeToHimselfException, CannotAttachSameChildToParentException
from program_management.ddd.domain.link import LinkIdentity
from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.service.read import get_program_tree_version_service
from program_management.ddd.service.write import paste_element_service
from program_management.tests.ddd.factories.domain.program_tree_version.mini_training.MINECON import MINECONFactory
from program_management.tests.ddd.factories.domain.program_tree_version.training.ARKE2M import ARKE2MFactory
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS1BA import OSIS1BAFactory
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from testing.testcases import DDDTestCase


class TestPasteLearningUnitNodeService(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree_version = OSIS1BAFactory()[0]
        self.tree = self.tree_version.tree

        self.learning_unit_node = NodeLearningUnitYearFactory(year=self.tree.root_node.year, persist=True)
        self.mini_training_version = MINECONFactory()[0]

        path = build_path(
            self.tree.root_node,
            self.tree.get_node_by_code_and_year("LOSIS101T", self.tree.root_node.year),
            self.tree.get_node_by_code_and_year("LOSIS102R", self.tree.root_node.year),
        )

        self.cmd = command.PasteElementCommand(
            node_to_paste_code=self.learning_unit_node.code,
            node_to_paste_year=self.learning_unit_node.year,
            path_where_to_paste=path,
            access_condition=True,
            is_mandatory=True,
            block="123",
            link_type=None,
            comment=None,
            comment_english=None,
            relative_credits=None
        )

    def test_cannot_paste_node_to_learning_unit_node(self):
        path = build_path(
            self.tree.root_node,
            self.tree.get_node_by_code_and_year("LOSIS101T", self.tree.root_node.year),
            self.tree.get_node_by_code_and_year("LOSIS102R", self.tree.root_node.year),
            self.tree.get_node_by_code_and_year("LDROI1001", self.tree.root_node.year),
        )
        cmd = attr.evolve(self.cmd, path_where_to_paste=path)

        with self.assertRaisesBusinessException(CannotPasteToLearningUnitException):
            paste_element_service.paste_element(cmd)

    def test_block_should_be_a_sequence_of_increasing_digit_comprised_between_1_and_6(self):
        cmd = attr.evolve(self.cmd, block="1298")

        with self.assertRaisesBusinessException(InvalidBlockException):
            paste_element_service.paste_element(cmd)

    def test_cannot_create_a_reference_link_with_a_learning_unit_as_child(self):
        cmd = attr.evolve(self.cmd, link_type=LinkTypes.REFERENCE.name)

        with self.assertRaisesBusinessException(ReferenceLinkNotAllowedWithLearningUnitException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_learning_unit_to_node_who_do_not_allow_learning_units_as_children(self):
        path = build_path(self.tree.root_node)
        cmd = attr.evolve(self.cmd, path_where_to_paste=path)

        with self.assertRaisesBusinessException(ChildTypeNotAuthorizedException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_group_year_node_to_node_who_do_not_allow_the_node_type(self):
        path = build_path(self.tree.root_node)
        cmd = attr.evolve(
            self.cmd,
            path_where_to_paste=path,
            node_to_paste_code=self.mini_training_version.tree.root_node.code
        )

        with self.assertRaisesBusinessException(ChildTypeNotAuthorizedException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_group_year_node_with_year_different_than_the_tree(self):
        node_to_paste = NodeGroupYearFactory(
            node_type=GroupType.SUB_GROUP,
            year=self.tree.root_node.year - 1,
            persist=True
        )
        cmd = attr.evolve(self.cmd, node_to_paste_code=node_to_paste.code, node_to_paste_year=node_to_paste.year)

        with self.assertRaisesBusinessException(ParentAndChildMustHaveSameAcademicYearException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_a_node_if_parent_has_reached_its_maximum_children_allowed_for_this_type(self):
        node_to_paste = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.tree.root_node.year,
            persist=True
        )

        cmd = attr.evolve(
            self.cmd,
            node_to_paste_code=node_to_paste.code,
            node_to_paste_year=node_to_paste.year,
            path_where_to_paste=build_path(self.tree.root_node)
        )

        with self.assertRaisesBusinessException(MaximumChildTypesReachedException):
            paste_element_service.paste_element(cmd)

    def test_cannot_have_node_containing_itself(self):
        cmd = attr.evolve(self.cmd, node_to_paste_code="LOSIS102R")

        with self.assertRaisesBusinessException(CannotPasteNodeToHimselfException):
            paste_element_service.paste_element(cmd)

    def test_cannot_have_multiple_occurrences_of_same_child(self):
        cmd = attr.evolve(self.cmd, node_to_paste_code="LDROI1001")

        with self.assertRaisesBusinessException(CannotAttachSameChildToParentException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_reference_link_if_referenced_children_not_authorized(self):
        cmd = attr.evolve(
            self.cmd,
            node_to_paste_code=self.mini_training_version.tree.root_node.code,
            link_type=LinkTypes.REFERENCE.name
        )

        with self.assertRaisesBusinessException(ChildTypeNotAuthorizedException):
            paste_element_service.paste_element(cmd)

    def test_cannot_paste_list_finalities_inside_list_finalities_if_max_finalities_is_already_reached(self):
        osis2m = OSIS2MFactory()[0].tree
        arke2m = ARKE2MFactory()[0].tree

        path = build_path(
            osis2m.root_node,
            osis2m.get_node_by_code_and_year("LOSIS104G", osis2m.root_node.year)
        )
        node_to_paste = arke2m.get_node_by_code_and_year("LARKE105G", osis2m.root_node.year)

        cmd = attr.evolve(self.cmd, path_where_to_paste=path, node_to_paste_code=node_to_paste.code)

        with self.assertRaisesBusinessException(MaximumChildTypesReachedException):
            paste_element_service.paste_element(cmd)

    def test_should_return_link_identity_of_link_newly_created(self):
        result = paste_element_service.paste_element(self.cmd)

        expected_identity = LinkIdentity(
            parent_year=self.tree.root_node.year,
            parent_code="LOSIS102R",
            child_year=self.tree.root_node.year,
            child_code=self.learning_unit_node.code
        )

        self.assertEqual(expected_identity, result)

    def test_should_persist_tree_with_new_link_created(self):
        link_identity = paste_element_service.paste_element(self.cmd)

        tree_version = self.reload_tree_version()

        tree_link_identities = [link.entity_id for link in tree_version.get_tree().get_all_links()]
        self.assertIn(link_identity, tree_link_identities)

    def test_should_set_is_mandatory_as_false_when_parent_is_a_list_minor_or_major_or_option(self):
        path = build_path(
            self.tree.root_node,
            self.tree.get_node_by_code_and_year("LOSIS101G", self.tree.root_node.year),
        )

        cmd = attr.evolve(
            self.cmd,
            path_where_to_paste=path,
            node_to_paste_code=self.mini_training_version.tree.root_node.code,
            is_mandatory=True
        )

        link_identity = paste_element_service.paste_element(cmd)
        tree_version = self.reload_tree_version()
        link = tree_version.get_tree().get_link_by_identity(link_identity)

        self.assertFalse(link.is_mandatory)

    def test_should_set_link_type_as_reference_when_parent_is_a_list_minor_or_major_and_child_is_minor_or_major(self):
        path = build_path(
            self.tree.root_node,
            self.tree.get_node_by_code_and_year("LOSIS101G", self.tree.root_node.year),
        )

        cmd = attr.evolve(
            self.cmd,
            path_where_to_paste=path,
            node_to_paste_code=self.mini_training_version.tree.root_node.code,
            link_type=None
        )

        link_identity = paste_element_service.paste_element(cmd)
        tree_version = self.reload_tree_version()
        link = tree_version.get_tree().get_link_by_identity(link_identity)

        self.assertTrue(link.is_reference())

    @skip("TODO")
    def test_cannot_paste_training_with_version_label_different(self):
        pass

    def test_cannot_paste_finality_with_end_date_greater_than_program(self):
        pass

    def test_cannot_paste_an_option_inside_finality_if_not_contained_in_list_option_of_program(self):
        pass

    def test_should_be_able_to_paste_a_list_minor_major_to_a_list_minor_major(self):
        node_types = [GroupType.MINOR_LIST_CHOICE, GroupType.MAJOR_LIST_CHOICE]
        path = build_path(
            self.tree.root_node,
            self.tree.get_node_by_code_and_year("LOSIS101G", self.tree.root_node.year),
        )
        for node_type in node_types:
            with self.subTest(node_type=node_type):
                node_to_paste = NodeGroupYearFactory(node_type=node_type, year=self.tree.root_node.year, persist=True)
                cmd = attr.evolve(
                    self.cmd,
                    path_where_to_paste=path,
                    node_to_paste_code=node_to_paste.code,
                    node_to_paste_year=node_to_paste.year
                )
                self.assertTrue(paste_element_service.paste_element(cmd))

    def reload_tree_version(self):
        tree_version = get_program_tree_version_service.get_program_tree_version(
            command.GetProgramTreeVersionCommand(
                year=self.tree_version.entity_id.year,
                acronym=self.tree_version.entity_id.offer_acronym,
                version_name=self.tree_version.entity_id.version_name,
                transition_name=self.tree_version.entity_id.transition_name,
            )
        )
        return tree_version
