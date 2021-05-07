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

from base.models.enums.education_group_types import TrainingType
from program_management.ddd.command import FillProgramTreeVersionContentFromProgramTreeVersionCommand
from program_management.ddd.domain.exception import ProgramTreeNonEmpty, InvalidTreeVersionToFillTo
from program_management.ddd.domain.node import factory as node_factory
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.service.write.fill_program_tree_version_content_from_program_tree_version_service import \
    fill_program_tree_version_content_from_program_tree_version
from program_management.tests.ddd.factories.domain.program_tree.BACHELOR_1BA import ProgramTreeBachelorFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree_version import SpecificProgramTreeVersionFactory, \
    SpecificTransitionProgramTreeVersionFactory, StandardProgramTreeVersionFactory
from testing.testcases import DDDTestCase

PAST_ACADEMIC_YEAR_YEAR = 2020
CURRENT_ACADEMIC_YEAR_YEAR = 2021
NEXT_ACADEMIC_YEAR_YEAR = 2022


@override_settings(YEAR_LIMIT_EDG_MODIFICATION=PAST_ACADEMIC_YEAR_YEAR)
class TestFillProgramTreeVersionContentFromLastYear(DDDTestCase):
    def setUp(self) -> None:
        self._init_fake_repos()

        self.tree_version_from = SpecificProgramTreeVersionFactory(
            tree=ProgramTreeBachelorFactory(current_year=CURRENT_ACADEMIC_YEAR_YEAR, end_year=NEXT_ACADEMIC_YEAR_YEAR)
        )
        self.tree_version_to_fill = SpecificProgramTreeVersionFactory(
            tree__root_node__code=self.tree_version_from.tree.root_node.code,
            tree__root_node__title=self.tree_version_from.entity_id.offer_acronym,
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__transition_name=NOT_A_TRANSITION,
            tree__root_node__node_type=TrainingType.BACHELOR,
            transition_name=NOT_A_TRANSITION
        )

        self.cmd = self._generate_cmd(self.tree_version_from, self.tree_version_to_fill)

        self.add_tree_version_to_repo(self.tree_version_from)
        self.add_tree_version_to_repo(self.tree_version_to_fill)

        self.mock_copy_cms()
        self.create_node_next_years(self.tree_version_from.tree.root_node.get_all_children_as_nodes())
        self.mock_copy_group()

    def create_node_next_years(self, nodes):
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

    def test_cannot_fill_non_empty_tree(self):
        tree_version_to_fill_to = SpecificProgramTreeVersionFactory(
            tree=ProgramTreeBachelorFactory(
                current_year=NEXT_ACADEMIC_YEAR_YEAR,
                end_year=NEXT_ACADEMIC_YEAR_YEAR
            )
        )
        tree_version_to_fill_from = SpecificProgramTreeVersionFactory(
            tree__root_node__code=tree_version_to_fill_to.tree.root_node.code,
            tree__root_node__year=CURRENT_ACADEMIC_YEAR_YEAR,
            tree__root_node__title=tree_version_to_fill_to.entity_id.offer_acronym,
        )

        self.add_tree_version_to_repo(tree_version_to_fill_to)
        self.add_tree_version_to_repo(tree_version_to_fill_from)

        cmd = self._generate_cmd(tree_version_to_fill_from, tree_version_to_fill_to)

        self.assertRaisesBusinessException(
            ProgramTreeNonEmpty,
            fill_program_tree_version_content_from_program_tree_version,
            cmd
        )

    def test_can_fill_standard_version_from_last_year(self):
        tree_version_from = StandardProgramTreeVersionFactory(
            tree=ProgramTreeBachelorFactory(current_year=CURRENT_ACADEMIC_YEAR_YEAR, end_year=NEXT_ACADEMIC_YEAR_YEAR)
        )
        tree_version_to_fill = StandardProgramTreeVersionFactory(
            tree__root_node__code=tree_version_from.tree.root_node.code,
            tree__root_node__title=tree_version_from.entity_id.offer_acronym,
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__transition_name=NOT_A_TRANSITION,
            tree__root_node__node_type=TrainingType.BACHELOR,
            transition_name=NOT_A_TRANSITION
        )
        self.add_tree_version_to_repo(tree_version_from)
        self.add_tree_version_to_repo(tree_version_to_fill)
        self.create_node_next_years(tree_version_from.tree.root_node.get_all_children_as_nodes())

        cmd = self._generate_cmd(tree_version_from, tree_version_to_fill)
        result = fill_program_tree_version_content_from_program_tree_version(cmd)
        self.assertTrue(result)

    def test_should_return_program_tree_version_identity_of_tree_filled(self):
        result = fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(self.tree_version_to_fill.entity_id, result)

    def test_should_persist(self):
        self.tree_version_from.tree.get_node("1|22").detach_child(
            self.tree_version_from.tree.get_node("1|22|32")
        )
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        expected = [
            attr.evolve(child_node.entity_id, year=NEXT_ACADEMIC_YEAR_YEAR)
            for child_node in self.tree_version_from.tree.root_node.get_all_children_as_nodes()
        ]
        actual = [
            child_node.entity_id
            for child_node in self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes()
        ]
        self.assertCountEqual(expected, actual)

    def test_if_learning_unit_is_not_present_in_next_year_then_attach_its_current_year_version(self):
        ue_node = NodeLearningUnitYearFactory(year=CURRENT_ACADEMIC_YEAR_YEAR, end_date=CURRENT_ACADEMIC_YEAR_YEAR)
        self.tree_version_from.tree.get_node("1|21|31").add_child(ue_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertIn(ue_node, self.tree_version_to_fill.tree.get_all_nodes())

    def test_do_not_copy_training_and_mini_training_that_ends_before_next_year(self):
        mini_training_node = NodeGroupYearFactory(
            year=CURRENT_ACADEMIC_YEAR_YEAR,
            end_date=CURRENT_ACADEMIC_YEAR_YEAR,
            minitraining=True
        )
        self.tree_version_from.tree.get_node("1|22").add_child(mini_training_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertNotIn(mini_training_node, self.tree_version_to_fill.tree.get_all_nodes())

    def test_always_copy_group_even_if_end_date_is_inferior_to_next_year(self):
        group_node = NodeGroupYearFactory(
            year=CURRENT_ACADEMIC_YEAR_YEAR,
            end_date=CURRENT_ACADEMIC_YEAR_YEAR,
            group=True
        )
        self.tree_version_from.tree.get_node("1|21").add_child(group_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        member = attr.evolve(group_node.entity_id, year=NEXT_ACADEMIC_YEAR_YEAR)
        containers = [
            child_node.entity_id
            for child_node in self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes()
        ]
        self.assertIn(member, containers)

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

    def test_do_not_overwrite_content_if_node_is_not_empty(self):
        subgroup_node = self.tree_version_from.tree.get_node("1|21|31")
        next_year_node = node_factory.copy_to_next_year(subgroup_node)
        self.add_node_to_repo(next_year_node)
        expected_link = LinkFactory(parent=next_year_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertIn(expected_link, self.tree_version_to_fill.tree.get_all_links())

    def _generate_cmd(
            self,
            tree_from: 'ProgramTreeVersion',
            tree_to: 'ProgramTreeVersion'
    ) -> 'FillProgramTreeVersionContentFromProgramTreeVersionCommand':
        return FillProgramTreeVersionContentFromProgramTreeVersionCommand(
            from_year=tree_from.entity_id.year,
            from_offer_acronym=tree_from.entity_id.offer_acronym,
            from_version_name=tree_from.entity_id.version_name,
            from_transition_name=tree_from.entity_id.transition_name,
            to_year=tree_to.entity_id.year,
            to_offer_acronym=tree_to.entity_id.offer_acronym,
            to_version_name=tree_to.entity_id.version_name,
            to_transition_name=tree_to.entity_id.transition_name
        )


@override_settings(YEAR_LIMIT_EDG_MODIFICATION=PAST_ACADEMIC_YEAR_YEAR)
class TestFillProgramTreeVersionContentFromSourceTreeVersion(DDDTestCase):
    def setUp(self) -> None:
        self._init_fake_repos()

        self.tree_version_from = SpecificProgramTreeVersionFactory(
            tree=ProgramTreeBachelorFactory(current_year=CURRENT_ACADEMIC_YEAR_YEAR, end_year=NEXT_ACADEMIC_YEAR_YEAR)
        )
        self.tree_version_to_fill = SpecificTransitionProgramTreeVersionFactory(
            tree__root_node__title=self.tree_version_from.entity_id.offer_acronym,
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )
        self.cmd = self._generate_cmd(self.tree_version_from, self.tree_version_to_fill)

        self.add_tree_version_to_repo(self.tree_version_from)
        self.add_tree_version_to_repo(self.tree_version_to_fill)

        self.create_node_next_years()
        self.mock_create_group()
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

    def mock_create_group(self):
        patcher = mock.patch(
            "education_group.ddd.service.write.create_group_service.create_orphan_group",
            side_effect=lambda node: self.add_node_to_repo(node)
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=CURRENT_ACADEMIC_YEAR_YEAR)
    def test_can_only_fill_content_of_tree_before_year_limit(self):
        tree_version_to_fill = StandardProgramTreeVersionFactory(
            tree__root_node__title=self.tree_version_from.entity_id.offer_acronym,
            tree__root_node__year=CURRENT_ACADEMIC_YEAR_YEAR
        )
        self.add_tree_version_to_repo(tree_version_to_fill)

        cmd = self._generate_cmd(self.tree_version_from, tree_version_to_fill)

        self.assertRaisesBusinessException(
            InvalidTreeVersionToFillTo,
            fill_program_tree_version_content_from_program_tree_version,
            cmd
        )

    def test_can_fill_transition_from_transition_past_year(self):
        tree_version_to_fill_from = SpecificTransitionProgramTreeVersionFactory(
            tree__root_node__year=CURRENT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )
        tree_version_to_fill = SpecificTransitionProgramTreeVersionFactory(
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__code=tree_version_to_fill_from.program_tree_identity.code,
            tree__root_node__node_type=TrainingType.BACHELOR
        )

        self.add_tree_version_to_repo(tree_version_to_fill_from)
        self.add_tree_version_to_repo(tree_version_to_fill)

        cmd = self._generate_cmd(tree_version_to_fill_from, tree_version_to_fill)

        self.assertTrue(
            fill_program_tree_version_content_from_program_tree_version(cmd)
        )

    def test_can_fill_transition_from_its_past_year_equivalent_non_transition(self):
        tree_version_to_fill_from = SpecificProgramTreeVersionFactory(
            tree__root_node__year=CURRENT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )
        tree_version_to_fill = SpecificTransitionProgramTreeVersionFactory(
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )

        self.add_tree_version_to_repo(tree_version_to_fill_from)
        self.add_tree_version_to_repo(tree_version_to_fill)

        cmd = self._generate_cmd(tree_version_to_fill_from, tree_version_to_fill)

        self.assertTrue(
            fill_program_tree_version_content_from_program_tree_version(cmd)
        )

    def test_can_fill_transition_from_its_same_year_equivalent_non_transition(self):
        tree_version_to_fill_from = SpecificProgramTreeVersionFactory(
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )
        tree_version_to_fill = SpecificTransitionProgramTreeVersionFactory(
            tree__root_node__year=NEXT_ACADEMIC_YEAR_YEAR,
            tree__root_node__node_type=TrainingType.BACHELOR
        )

        self.add_tree_version_to_repo(tree_version_to_fill_from)
        self.add_tree_version_to_repo(tree_version_to_fill)

        cmd = self._generate_cmd(tree_version_to_fill_from, tree_version_to_fill)

        self.assertTrue(
            fill_program_tree_version_content_from_program_tree_version(cmd)
        )

    def test_cannot_fill_non_empty_tree(self):
        tree_version_to_fill_to = SpecificTransitionProgramTreeVersionFactory(
            tree=ProgramTreeBachelorFactory(
                current_year=NEXT_ACADEMIC_YEAR_YEAR,
                end_year=NEXT_ACADEMIC_YEAR_YEAR
            )
        )
        tree_version_to_fill_from = SpecificProgramTreeVersionFactory(
            tree__root_node__code=tree_version_to_fill_to.tree.root_node.code,
            tree__root_node__year=CURRENT_ACADEMIC_YEAR_YEAR
        )

        self.add_tree_version_to_repo(tree_version_to_fill_to)
        self.add_tree_version_to_repo(tree_version_to_fill_from)

        cmd = self._generate_cmd(tree_version_to_fill_from, tree_version_to_fill_to)

        self.assertRaisesBusinessException(
            ProgramTreeNonEmpty,
            fill_program_tree_version_content_from_program_tree_version,
            cmd
        )

    def test_should_return_program_tree_version_identity_of_tree_filled(self):
        result = fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(self.tree_version_to_fill.entity_id, result)

    def test_should_persist(self):
        self.tree_version_from.tree.get_node("1|22").detach_child(
            self.tree_version_from.tree.get_node("1|22|32")
        )
        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertEqual(
            len(self.tree_version_from.tree.root_node.get_all_children_as_nodes()),
            len(self.tree_version_to_fill.tree.root_node.get_all_children_as_nodes())
        )

    def test_if_learning_unit_is_not_present_in_next_year_then_attach_its_current_year_version(self):
        ue_node = NodeLearningUnitYearFactory(year=CURRENT_ACADEMIC_YEAR_YEAR, end_date=CURRENT_ACADEMIC_YEAR_YEAR)
        self.tree_version_from.tree.get_node("1|21|31").add_child(ue_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertIn(ue_node, self.tree_version_to_fill.tree.get_all_nodes())

    def test_do_not_copy_training_and_mini_training_that_ends_before_next_year(self):
        mini_training_node = NodeGroupYearFactory(
            year=CURRENT_ACADEMIC_YEAR_YEAR,
            end_date=CURRENT_ACADEMIC_YEAR_YEAR,
            minitraining=True
        )
        self.tree_version_from.tree.get_node("1|22").add_child(mini_training_node)

        fill_program_tree_version_content_from_program_tree_version(self.cmd)

        self.assertNotIn(mini_training_node, self.tree_version_to_fill.tree.get_all_nodes())

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

    def _generate_cmd(
            self,
            tree_from: 'ProgramTreeVersion',
            tree_to: 'ProgramTreeVersion',
    ) -> 'FillProgramTreeVersionContentFromProgramTreeVersionCommand':
        return FillProgramTreeVersionContentFromProgramTreeVersionCommand(
            from_year=tree_from.entity_id.year,
            from_offer_acronym=tree_from.entity_id.offer_acronym,
            from_version_name=tree_from.entity_id.version_name,
            from_transition_name=tree_from.entity_id.transition_name,
            to_year=tree_to.entity_id.year,
            to_offer_acronym=tree_to.entity_id.offer_acronym,
            to_version_name=tree_to.entity_id.version_name,
            to_transition_name=tree_to.entity_id.transition_name
        )
