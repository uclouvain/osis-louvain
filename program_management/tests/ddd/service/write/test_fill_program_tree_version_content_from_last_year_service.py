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
from unittest import skip

import attr
import mock
from django.test import override_settings

from program_management.ddd.command import FillProgramTreeVersionContentFromProgramTreeVersionCommand, \
    GetProgramTreeVersionCommand
from program_management.ddd.domain.exception import ProgramTreeNonEmpty, MinimumEditableYearException
from program_management.ddd.domain.node import factory as node_factory
from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.service.read import get_program_tree_version_service
from program_management.ddd.service.write.fill_program_tree_version_content_from_program_tree_version_service import \
    fill_program_tree_version_content_from_program_tree_version
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory, \
    OSIS2MSpecificVersionFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from testing.testcases import DDDTestCase

PAST_ACADEMIC_YEAR_YEAR = 2020
CURRENT_ACADEMIC_YEAR_YEAR = 2021
NEXT_ACADEMIC_YEAR_YEAR = 2022


class TestFillProgramTreeVersionContentFromLastYear(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        OSIS2MFactory()[0]
        tree_versions = OSIS2MSpecificVersionFactory()
        self.tree_version_from = tree_versions[0]
        self.tree_version_to_fill = tree_versions[1]

        self.cmd = FillProgramTreeVersionContentFromProgramTreeVersionCommand(
            from_year=self.tree_version_from.entity_id.year,
            from_offer_acronym=self.tree_version_from.entity_id.offer_acronym,
            from_version_name=self.tree_version_from.entity_id.version_name,
            from_transition_name=self.tree_version_from.entity_id.transition_name,
            to_year=self.tree_version_to_fill.entity_id.year,
            to_offer_acronym=self.tree_version_to_fill.entity_id.offer_acronym,
            to_version_name=self.tree_version_to_fill.entity_id.version_name,
            to_transition_name=self.tree_version_to_fill.entity_id.transition_name
        )

        self.mock_copy_cms()
        self.create_node_next_years()

    def create_node_next_years(self):
        nodes = self.tree_version_from.tree.root_node.get_all_children_as_nodes()
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

    def test_cannot_fill_non_empty_tree(self):
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        with self.assertRaisesBusinessException(ProgramTreeNonEmpty):
            fill_program_tree_version_content_from_program_tree_version(self.cmd)

    def test_if_learning_unit_is_not_present_in_next_year_then_attach_its_current_year_version(self):
        ue_node = NodeLearningUnitYearFactory(year=self.cmd.from_year, end_date=self.cmd.from_year)
        path = build_path(
            self.tree_version_from.tree.root_node,
            self.tree_version_from.tree.get_node_by_code_and_year("LOSIS202T", self.cmd.from_year)
        )
        self.tree_version_from.tree.get_node(path).add_child(ue_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertIn(ue_node, self.tree_version_to_fill.tree.get_all_nodes())

    def test_do_not_copy_training_and_mini_training_that_ends_before_next_year(self):
        training_node = NodeGroupYearFactory(year=self.cmd.from_year, end_date=self.cmd.from_year)
        path = build_path(
            self.tree_version_from.tree.root_node,
            self.tree_version_from.tree.get_node_by_code_and_year("LOSIS105G", self.cmd.from_year)
        )
        self.tree_version_from.tree.get_node(path).add_child(training_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertNotIn(training_node, self.tree_version_to_fill.tree.get_all_nodes())

    def test_always_copy_group_even_if_end_date_is_inferior_to_next_year(self):
        group_node = NodeGroupYearFactory(year=self.cmd.from_year, end_date=self.cmd.from_year, group=True)
        path = build_path(
            self.tree_version_from.tree.root_node,
            self.tree_version_from.tree.get_node_by_code_and_year("LOSIS202T", self.cmd.from_year)
        )
        self.tree_version_from.tree.get_node(path).add_child(group_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertTrue(self.tree_version_to_fill.tree.get_node_by_code_and_year(group_node.code, self.cmd.to_year))

    @skip("Refactor")
    def test_do_not_copy_content_of_reference_child(self):
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        children_of_reference_link = self.tree_version_from.tree.get_node("1|22|32").get_all_children_as_nodes()
        entities_ids = {
            attr.evolve(child_node.entity_id, year=NEXT_ACADEMIC_YEAR_YEAR)
            for child_node in children_of_reference_link
        }

        tree_entities_ids = {
            child_node.entity_id
            for child_node in self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes()
        }
        self.assertFalse(tree_entities_ids.intersection(entities_ids))

    @skip("Refactor")
    def test_do_not_overwrite_content_if_node_is_not_empty(self):
        subgroup_node = self.tree_version_from.tree.get_node_by_code_and_year("LOSIS202R", self.cmd.from_year)
        next_year_node = node_factory.copy_to_next_year(subgroup_node)
        self.add_node_to_repo(next_year_node)
        expected_link = LinkFactory(parent=next_year_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertIn(expected_link, self.tree_version_to_fill.tree.get_all_links())

    def test_should_return_program_tree_version_identity_of_tree_filled(self):
        result = fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(self.tree_version_to_fill.entity_id, result)

    def test_should_persist(self):
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        actual = [
            child_node.entity_id
            for child_node in self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes()
        ]
        expected = [
            attr.evolve(child_node.entity_id, year=self.cmd.to_year)
            for child_node in self.tree_version_from.tree.root_node.get_all_children_as_nodes()
        ]
        self.assertCountEqual(expected, actual)


class TestFillTransitionProgramTreeVersionContent(DDDTestCase):
    def setUp(self) -> None:
        super().setUp()
        standard = OSIS2MFactory()[0]
        specific_version = OSIS2MSpecificVersionFactory()[0]

        self.transitions = OSIS2MSpecificVersionFactory.create_transition_from_tree_version(specific_version)

        finality_tree_version = get_program_tree_version_service.get_program_tree_version(
            GetProgramTreeVersionCommand(
                year=specific_version.entity_id.year,
                acronym="OSIS2MD",
                version_name=specific_version.version_name,
                transition_name=specific_version.transition_name
            )
        )

        OSIS2MSpecificVersionFactory.create_transition_from_tree_version(
            finality_tree_version
        )

        self.tree_version_from = specific_version
        self.tree_version_to_fill = self.transitions[1]

        self.cmd = FillProgramTreeVersionContentFromProgramTreeVersionCommand(
            from_year=self.tree_version_from.entity_id.year,
            from_offer_acronym=self.tree_version_from.entity_id.offer_acronym,
            from_version_name=self.tree_version_from.entity_id.version_name,
            from_transition_name=self.tree_version_from.entity_id.transition_name,
            to_year=self.tree_version_to_fill.entity_id.year,
            to_offer_acronym=self.tree_version_to_fill.entity_id.offer_acronym,
            to_version_name=self.tree_version_to_fill.entity_id.version_name,
            to_transition_name=self.tree_version_to_fill.entity_id.transition_name
        )

        self.create_node_next_years()
        self.mock_generate_code()
        self.mock_copy_cms()

    def create_node_next_years(self):
        nodes = self.tree_version_from.tree.root_node.get_all_children_as_nodes()
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

    def mock_generate_code(self):
        patcher = mock.patch(
            "program_management.ddd.domain.node.GenerateNodeCode.generate_from_parent_node",
            side_effect=lambda parent_node, **kwargs: "T" + parent_node.code
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @skip("TODO")
    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=CURRENT_ACADEMIC_YEAR_YEAR)
    def test_can_only_fill_content_of_tree_before_year_limit(self):
        with self.assertRaisesBusinessException(MinimumEditableYearException):
            fill_program_tree_version_content_from_program_tree_version(self.cmd)

    def test_can_fill_transition_from_transition_past_year(self):
        cmd = attr.evolve(self.cmd, from_transition_name=self.transitions[0].entity_id.transition_name)

        self.assertTrue(fill_program_tree_version_content_from_program_tree_version(cmd))

    def test_can_fill_transition_from_its_past_year_equivalent_non_transition(self):
        self.assertTrue(fill_program_tree_version_content_from_program_tree_version(self.cmd))

    def test_can_fill_transition_from_its_same_year_equivalent_non_transition(self):
        cmd = attr.evolve(self.cmd, from_year=self.cmd.to_year)

        self.assertTrue(fill_program_tree_version_content_from_program_tree_version(cmd))

    @skip("TODO")
    def test_cannot_fill_non_empty_tree(self):
        with self.assertRaisesBusinessException(ProgramTreeNonEmpty):
            fill_program_tree_version_content_from_program_tree_version(self.cmd)

    def test_cannot_fill_transition_if_no_finalities_without_transitions(self):
        pass

    def test_if_learning_unit_is_not_present_in_next_year_then_attach_its_current_year_version(self):
        pass

    def test_do_not_copy_training_and_mini_training_that_ends_before_next_year(self):
        pass

    def test_convert_reference_link_into_normal_link(self):
        pass

    def test_should_return_program_tree_version_identity_of_tree_filled(self):
        result = fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(self.tree_version_to_fill.entity_id, result)

    def test_should_persist(self):
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(
            len(self.tree_version_from.tree.root_node.get_all_children_as_nodes()),
            len(self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes())
        )

    def test_in_case_of_transition_generate_new_group_with_code_beginning_by_T(self):
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        group_nodes = [
            node for node in self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes()
            if node.is_group()
        ]
        group_codes = [node.code for node in group_nodes]
        does_all_group_nodes_start_with_t = all(
            [code.startswith("T") for code in group_codes]
        )
        self.assertTrue(does_all_group_nodes_start_with_t)
