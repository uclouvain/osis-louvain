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
from unittest.mock import patch
from unittest import mock

from django.test import TestCase

from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from program_management.ddd.domain.node import NodeEducationGroupYear, NodeLearningUnitYear, NodeGroupYear
from program_management.ddd.repositories import persist_tree, load_tree
from program_management.ddd.validators._authorized_relationship import DetachAuthorizedRelationshipValidator
from program_management.ddd.validators.validators_by_business_action import DetachNodeValidatorList
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory, \
    NodeEducationGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestPersistTree(TestCase):
    def setUp(self):
        academic_year = AcademicYearFactory(current=True)

        self.training_version = EducationGroupVersionFactory()

        self.root_group = ElementGroupYearFactory(group_year=self.training_version.root_group)
        self.common_core_element = ElementGroupYearFactory(group_year__academic_year=academic_year)
        self.learning_unit_year_element = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year=academic_year
        )

        self.root_node = NodeGroupYearFactory(
            node_id=self.root_group.pk,
            code=self.root_group.group_year.partial_acronym,
            year=self.root_group.group_year.academic_year.year
        )
        self.common_core_node = NodeGroupYearFactory(
            node_id=self.common_core_element.pk,
            code=self.common_core_element.group_year.partial_acronym,
            year=self.common_core_element.group_year.academic_year.year
        )
        self.learning_unit_year_node = NodeLearningUnitYearFactory(
            node_id=self.learning_unit_year_element.pk,
            code=self.learning_unit_year_element.learning_unit_year.acronym,
            year=self.learning_unit_year_element.learning_unit_year.academic_year.year
        )

    def test_persist_tree_from_scratch(self):
        self.common_core_node.add_child(self.learning_unit_year_node)
        self.root_node.add_child(self.common_core_node)
        tree = ProgramTreeFactory(root_node=self.root_node)

        persist_tree.persist(tree)

        link_root_with_common_core = GroupElementYear.objects.filter(
            parent_element_id=self.root_node.node_id,
            child_element_id=self.common_core_node.node_id,
        )
        self.assertTrue(link_root_with_common_core.exists())

        link_common_core_with_learn_unit = GroupElementYear.objects.filter(
            parent_element_id=self.common_core_node.node_id,
            child_element_id=self.learning_unit_year_node.node_id,
        )
        self.assertTrue(link_common_core_with_learn_unit.exists())

    def test_save_when_first_link_exists_and_second_one_does_not(self):
        GroupElementYearFactory(parent_element=self.root_group, child_element=self.common_core_element)
        tree = load_tree.load(self.root_node.node_id)

        # Append UE to common core
        tree.root_node.children[0].child.add_child(self.learning_unit_year_node)

        persist_tree.persist(tree)

        self.assertTrue(
            GroupElementYear.objects.filter(
                parent_element=self.common_core_node.node_id,
                child_element=self.learning_unit_year_node.node_id
            ).exists()
        )

    @patch("program_management.ddd.repositories.persist_tree.__persist_group_element_year")
    def test_save_when_link_has_not_changed(self, mock):
        GroupElementYearFactory(parent_element=self.root_group, child_element=self.common_core_element)
        tree = load_tree.load(self.root_node.node_id)
        persist_tree.persist(tree)
        assertion_msg = "No changes made, so function GroupelementYear.save() should not have been called"
        self.assertFalse(mock.called, assertion_msg)

    @patch("program_management.ddd.repositories.persist_tree.__persist_group_element_year")
    def test_save_when_link_has_changed(self, mock):
        GroupElementYearFactory(parent_element=self.root_group, child_element=self.common_core_element)
        tree = load_tree.load(self.root_node.node_id)
        tree.root_node.children[0]._has_changed = True  # Made some changes
        persist_tree.persist(tree)
        assertion_msg = """
            Changes were triggered in the Link object, so function GroupelementYear.save() should have been called
        """
        self.assertTrue(mock.called, assertion_msg)

    @patch.object(DetachNodeValidatorList, 'validate')
    def test_delete_when_1_link_has_been_deleted(self, mock_detach):
        mock_detach.return_value = None
        GroupElementYearFactory(parent_element=self.root_group, child_element=self.common_core_element)
        node_to_detach = self.common_core_node
        qs_link_will_be_detached = GroupElementYear.objects.filter(child_element_id=node_to_detach.pk)
        self.assertEqual(qs_link_will_be_detached.count(), 1)

        tree = load_tree.load(self.root_node.node_id)

        path_to_detach = "|".join([str(self.root_node.pk), str(node_to_detach.pk)])
        tree.detach_node(path_to_detach, mock.Mock())
        persist_tree.persist(tree)
        self.assertEqual(qs_link_will_be_detached.count(), 0)

    @patch("program_management.ddd.repositories.persist_tree.__delete_group_element_year")
    def test_delete_when_nothing_has_been_deleted(self, mock):
        GroupElementYearFactory(parent_element=self.root_group, child_element=self.common_core_element)
        tree = load_tree.load(self.root_node.node_id)
        persist_tree.persist(tree)
        assertion_msg = "No changes made, so function GroupelementYear.delete() should not have been called"
        self.assertFalse(mock.called, assertion_msg)


class TestPersistPrerequisites(TestCase):
    @patch("program_management.ddd.repositories._persist_prerequisite.persist")
    def test_call_persist_(self, mock_persist_prerequisite):
        tree = ProgramTreeFactory()
        LinkFactory(parent=tree.root_node, child=NodeLearningUnitYearFactory())

        persist_tree.persist(tree)

        mock_persist_prerequisite.assert_called_once_with(tree)

    @patch("program_management.ddd.repositories._persist_prerequisite._persist")
    @patch("program_management.ddd.repositories.persist_tree.__delete_group_element_year")
    def test_should_call_persist_prerequisites_on_all_children_when_link_deleted(
            self,
            mock_delete_group_element_year,
            mock_persist_prerequisite):
        root_version = EducationGroupVersionFactory()
        link_1 = GroupElementYearFactory(parent_element__group_year=root_version.root_group)
        link_2_1 = GroupElementYearChildLeafFactory(parent_element=link_1.child_element)
        link_2_2 = GroupElementYearChildLeafFactory(parent_element=link_1.child_element)

        tree = load_tree.load(link_1.parent_element.id)
        root_node_child = tree.root_node.children_as_nodes[0]
        tree.root_node.detach_child(root_node_child)

        persist_tree.persist(tree)
        number_learning_unit_removed = 2
        self.assertEqual(
            mock_persist_prerequisite.call_count,
            number_learning_unit_removed
        )
