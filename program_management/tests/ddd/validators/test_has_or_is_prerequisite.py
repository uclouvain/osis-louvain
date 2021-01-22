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
from unittest import mock

from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.ddd.domain.exception import CannotDetachLearningUnitsWhoArePrerequisiteException, \
    CannotDetachLearningUnitsWhoHavePrerequisiteException
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.repositories.tree_prerequisites import TreePrerequisitesRepository
from program_management.ddd.validators._has_or_is_prerequisite import _IsPrerequisiteValidator, \
    _HasPrerequisiteValidator, IsHasPrerequisiteForAllTreesValidator
from program_management.tests.ddd.factories.domain.prerequisite.prerequisite import PrerequisitesFactory
from program_management.tests.ddd.factories.domain.program_tree.LADRT100I_MINADROI import ProgramTreeMINADROIFactory
from program_management.tests.ddd.factories.domain.program_tree.LDROI100B_DROI1BA import ProgramTreeDROI1BAFactory
from program_management.tests.ddd.factories.domain.program_tree.LDROI200M_DROI2M import ProgramTreeDROI2MFactory
from program_management.tests.ddd.factories.domain.program_tree.LDROP221O_OPTDROI2MAR import \
    ProgramTreeOptionLDROP221OFactory
from program_management.tests.ddd.factories.domain.program_tree.LSPED200M_SPED2M import ProgramTreeSPED2MFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestIsPrerequisiteValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        self.year = 2020
        self.tree = ProgramTreeDROI2MFactory(root_node__year=self.year)
        self.ldrop2011 = self.tree.get_node_by_code_and_year(code="LDROP2011", year=self.year)
        self.ldroi2101 = self.tree.get_node_by_code_and_year(code="LDROI2101", year=self.year)
        self.ldrop100t = self.tree.get_node_by_code_and_year(code="LDROP100T", year=self.year)
        self.ldroi220t = self.tree.get_node_by_code_and_year(code="LDROI220T", year=self.year)

    def test_should_not_raise_exception_when_children_of_node_to_detach_are_not_prerequisites(self):
        tree = copy.deepcopy(self.tree)
        node_without_prerequisite = self.tree.get_node_by_code_and_year(code="LDROP2013", year=self.year)
        validator = _IsPrerequisiteValidator(tree, node_to_detach=node_without_prerequisite)
        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_children_of_node_to_detach_are_prerequisites(self):
        tree = copy.deepcopy(self.tree)
        tree.set_prerequisite(
            prerequisite_expression="LDROI2101",
            node_having_prerequisites=self.ldrop2011
        )

        node_containing_child_that_is_prerequisite = self.ldroi220t

        with self.assertRaises(CannotDetachLearningUnitsWhoArePrerequisiteException):
            _IsPrerequisiteValidator(tree, node_to_detach=node_containing_child_that_is_prerequisite).validate()

    def test_should_raise_exception_when_node_to_detach_is_prerequisite(self):
        tree = copy.deepcopy(self.tree)
        tree.set_prerequisite(
            prerequisite_expression="LDROI2101",
            node_having_prerequisites=self.ldrop2011
        )

        node_that_is_prerequisite = self.ldroi2101

        with self.assertRaises(CannotDetachLearningUnitsWhoArePrerequisiteException):
            _IsPrerequisiteValidator(tree, node_to_detach=node_that_is_prerequisite).validate()

    def test_should_raise_exception_when_node_to_detach_is_prerequisite_twice_with_same_parent(self):
        tree = ProgramTreeDROI2MFactory(root_node__year=self.year)
        ldroi2101 = tree.get_node_by_code_and_year(code="LDROI2101", year=self.year)

        subgroup = NodeGroupYearFactory(
            code='LDROI111G',
            title='SUBGROUP_REUSED_TWICE',
            node_type=GroupType.SUB_GROUP,
            end_year=tree.root_node.end_year,
            year=self.year,
        )
        ldroi9999 = NodeLearningUnitYearFactory(code='LDROI9999', year=self.year, end_date=tree.root_node.end_year)

        ldroi220t = tree.get_node_by_code_and_year(code="LDROI220T", year=self.year)
        ldrop100t = tree.get_node_by_code_and_year(code="LDROP100T", year=self.year)
        LinkFactory(
            parent=subgroup,
            child=ldroi9999  # learning unit is used in subgroup
        )
        LinkFactory(
            parent=ldroi220t,
            child=subgroup  # The subgroup is used first time here
        )
        LinkFactory(
            parent=ldrop100t,
            child=subgroup  # The subgroup is used second time here
        )

        tree.set_prerequisite(
            prerequisite_expression=ldroi2101.code,
            node_having_prerequisites=ldroi9999
        )
        node_that_is_prerequisite_and_used_twice_in_tree = ldroi9999
        self.assertTrue(tree.count_usages_distinct(ldroi9999) == 1)

        assertion = """
            The Learning unit LDROI2101 appears 2 times in tree, but with the same parent.
            In this case, the validator should raise exception
        """
        with self.assertRaises(CannotDetachLearningUnitsWhoArePrerequisiteException):
            _IsPrerequisiteValidator(
                tree,
                node_to_detach=ldroi2101
            ).validate()

        with self.assertRaises(CannotDetachLearningUnitsWhoHavePrerequisiteException):
            _HasPrerequisiteValidator(tree, node_to_detach=ldroi9999).validate()

    def test_should_not_raise_exception_when_node_to_detach_is_prerequisite_twice_with_different_parent(self):
        tree = ProgramTreeDROI2MFactory(root_node__year=self.year)
        ldrop2011 = tree.get_node_by_code_and_year(code="LDROP2011", year=self.year)
        ldroi2101 = tree.get_node_by_code_and_year(code="LDROI2101", year=self.year)
        ldrop100t = tree.get_node_by_code_and_year(code="LDROP100T", year=self.year)
        LinkFactory(
            parent=ldrop100t,
            child=ldroi2101  # learning unit used twice with different parent (LDROP100T)
        )

        tree.set_prerequisite(
            prerequisite_expression="LDROI2101",
            node_having_prerequisites=ldrop2011
        )
        node_that_is_prerequisite_and_used_twice_in_tree = ldroi2101
        self.assertTrue(tree.count_usages_distinct(node_that_is_prerequisite_and_used_twice_in_tree) == 2)

        assertion = """
            While the prerequisite is used more than once in the same tree with different parents, we can detach it.
        """
        self.assertValidatorNotRaises(
            _IsPrerequisiteValidator(tree, node_to_detach=node_that_is_prerequisite_and_used_twice_in_tree)
        )

    @mock.patch.object(TreePrerequisitesRepository, 'search')
    @mock.patch.object(ProgramTreeRepository, 'search')
    def test_should_not_raise_when_node_to_detach_has_prerequisite_and_is_program_tree(
            self,
            mock_search_trees,
            mock_search_prerequisites
    ):
        tree = copy.deepcopy(self.tree)

        mini_training_node = tree.get_node_by_code_and_year(code="LDROP221O", year=self.year)
        mini_training_tree = ProgramTreeFactory(root_node=mini_training_node)
        PrerequisitesFactory.produce_inside_tree(
            context_tree=mini_training_tree,
            node_having_prerequisite=self.ldrop2011.entity_id,
            nodes_that_are_prequisites=[tree.get_node_by_code_and_year(code="LDROP2012", year=self.year)]
        )

        mock_search_trees.return_value = [tree]
        mock_search_prerequisites.return_value = [mini_training_tree.prerequisites]

        assertion = """
            The node to detach is a minitraining where there are prerequisite only inside itself.
            In this case, we can detach it becauses prerequisites are not pertinent in the cotnext of the DROI2M.
        """
        self.assertValidatorNotRaises(
            IsHasPrerequisiteForAllTreesValidator(
                node_to_detach=mini_training_node,
                parent_node=tree.get_node_by_code_and_year(code="LDROI100G", year=self.year),
                program_tree_repository=ProgramTreeRepository(),
                prerequisite_repository=TreePrerequisitesRepository(),
            )
        )

    @mock.patch.object(TreePrerequisitesRepository, 'search')
    @mock.patch.object(ProgramTreeRepository, 'search')
    def test_should_not_raise_when_prerequisite_is_in_minor_and_reused_in_TC_of_other_tree(
            self,
            mock_search_trees,
            mock_search_prerequisites
    ):
        droi1ba = ProgramTreeDROI1BAFactory(root_node__year=self.year)
        ldroi900t = droi1ba.get_node_by_code_and_year(code="LDROI900T", year=self.year)
        ldroi104g = droi1ba.get_node_by_code_and_year(code="LDROI104G", year=self.year)

        minadroi = ProgramTreeMINADROIFactory(root_node__year=self.year)
        ldroi1222 = minadroi.get_node_by_code_and_year(code="LDROI1222", year=self.year)
        PrerequisitesFactory.produce_inside_tree(
            context_tree=minadroi,
            node_having_prerequisite=ldroi1222.entity_id,
            nodes_that_are_prequisites=[minadroi.get_node_by_code_and_year(code="LDROI1223", year=self.year)]
        )

        LinkFactory(
            parent=ldroi104g,
            child=minadroi.root_node,
        )  # Add minor inside bachelor
        LinkFactory(
            parent=ldroi900t,
            child=ldroi1222,  # Add UE inside TC of bachelor (reused twice)
        )

        mock_search_trees.return_value = [minadroi]
        mock_search_prerequisites.return_value = [minadroi.prerequisites]

        """
        LDROI1222 has prerequisites only in the context of MINADROI (not in context of LDROI900T contained in DROI1BA).
        So the validator should not raise exception
        """
        self.assertValidatorNotRaises(
            IsHasPrerequisiteForAllTreesValidator(
                node_to_detach=ldroi1222,
                parent_node=ldroi900t,
                program_tree_repository=ProgramTreeRepository(),
                prerequisite_repository=TreePrerequisitesRepository(),
            )
        )
        self.assertDictEqual(
            mock_search_trees.call_args[1],
            {'entity_ids': [minadroi.entity_id]},
            "Should only search trees that have prerequisites for node to detach"
        )

    @mock.patch.object(TreePrerequisitesRepository, 'search')
    @mock.patch.object(ProgramTreeRepository, 'search')
    def test_should_raise_when_prerequisite_is_in_subgroup_minor_and_reused_in_TC_of_bachelor(
            self,
            mock_search_trees,
            mock_search_prerequisites
    ):
        droi1ba = ProgramTreeDROI1BAFactory(root_node__year=self.year)
        ldroi900t = droi1ba.get_node_by_code_and_year(code="LDROI900T", year=self.year)

        minadroi = ProgramTreeMINADROIFactory(root_node__year=self.year)
        ladrt102r = minadroi.get_node_by_code_and_year(code="LADRT102R", year=self.year)
        ldroi1222 = minadroi.get_node_by_code_and_year(code="LDROI1222", year=self.year)
        PrerequisitesFactory.produce_inside_tree(
            context_tree=minadroi,
            node_having_prerequisite=ldroi1222.entity_id,
            nodes_that_are_prequisites=[minadroi.get_node_by_code_and_year(code="LDROI1223", year=self.year)]
        )

        self.assertIsNone(
            droi1ba.get_node_by_code_and_year(code=minadroi.root_node.code, year=self.year),
            "To run this test, the minor must be outside the tree"
        )

        LinkFactory(
            parent=ldroi900t,
            child=ladrt102r,  # Add subgroup containing prerequisite inside TC of bachelor
        )

        mock_search_prerequisites.return_value = [minadroi.prerequisites]
        mock_search_trees.return_value = [minadroi]

        with self.assertRaises(CannotDetachLearningUnitsWhoHavePrerequisiteException):
            """
            In context of DROI1BA, LADRT102R does not contain any nodes that have prerequisites.
            But in context of MINADROI, LADRT102R contains nodes that have prerequisites.
            In this case, the validator must raise an error.
            """
            IsHasPrerequisiteForAllTreesValidator(
                node_to_detach=ldroi1222,
                parent_node=ladrt102r,
                program_tree_repository=ProgramTreeRepository(),
                prerequisite_repository=TreePrerequisitesRepository(),
            ).validate()
        self.assertDictEqual(
            mock_search_trees.call_args[1],
            {'entity_ids': [minadroi.entity_id]},
            "Should only search trees that have prerequisites for node to detach"
        )

    @mock.patch.object(TreePrerequisitesRepository, 'search')
    @mock.patch.object(ProgramTreeRepository, 'search')
    def test_should_raise_when_prerequisite_is_in_DROI2M_option_and_reused_in_other_2M(
            self,
            mock_search_trees,
            mock_search_prerequisites
    ):
        droi2m = copy.deepcopy(self.tree)
        option = ProgramTreeOptionLDROP221OFactory(root_node__year=self.year)
        ldrop2011 = option.get_node_by_code_and_year(code="LDROP2011", year=self.year)

        PrerequisitesFactory.produce_inside_tree(
            context_tree=droi2m,
            node_having_prerequisite=ldrop2011.entity_id,
            nodes_that_are_prequisites=[self.ldroi2101]
        )  # Set prerequisite between UE in option and UE in DROI2M

        sped2m = ProgramTreeSPED2MFactory(root_node__year=self.year)
        LinkFactory(
            parent=sped2m.get_node_by_code_and_year(code="LSPED103G", year=self.year),
            child=option.root_node
        )  # Other 2M is reusing the same option

        mock_search_prerequisites.return_value = [droi2m.prerequisites]
        mock_search_trees.return_value = [droi2m]

        with self.assertRaises(CannotDetachLearningUnitsWhoHavePrerequisiteException):
            """
            In context of DROI2M, LDROI2101 (inside DROI2M) is prerequisite of LDROP2011 (inside option used in DROI2M).
            But in context of SPED2M, there is no prerequisites.
            When we try to detach LDROI2101 inside SPED2M, the validator must raise an error.
            """
            IsHasPrerequisiteForAllTreesValidator(
                node_to_detach=ldrop2011,
                parent_node=option.get_node_by_code_and_year(code="LDROP100T", year=self.year),
                program_tree_repository=ProgramTreeRepository(),
                prerequisite_repository=TreePrerequisitesRepository(),
            ).validate()
        self.assertDictEqual(
            mock_search_trees.call_args[1],
            {'entity_ids': [droi2m.entity_id]},
            "Should only search trees that have prerequisites for node to detach"
        )


class TestHasPrerequisiteValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        self.year = 2020
        self.tree_droi2m = ProgramTreeDROI2MFactory(root_node__year=self.year)
        self.node_is_prerequisite = self.tree_droi2m.get_node_by_code_and_year(code="LDROI2101", year=self.year)
        self.node_has_prerequisite = self.tree_droi2m.get_node_by_code_and_year(code="LDROP2011", year=self.year)
        PrerequisitesFactory.produce_inside_tree(
            context_tree=self.tree_droi2m,
            node_having_prerequisite=self.node_has_prerequisite.entity_id,
            nodes_that_are_prequisites=[self.node_is_prerequisite.entity_id]
        )

    def test_should_not_raise_exception_when_children_of_node_to_detach_do_not_have_prerequisites(self):
        inexisting_node_in_tree = NodeGroupYearFactory()

        validator = _HasPrerequisiteValidator(self.tree_droi2m, node_to_detach=inexisting_node_in_tree)
        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_children_of_node_to_detach_have_prerequisites(self):
        parent_of_node_that_has_prerequisite = self.tree_droi2m.get_node_by_code_and_year(
            code="LDROP100T",
            year=self.year
        )

        with self.assertRaises(CannotDetachLearningUnitsWhoHavePrerequisiteException):
            _HasPrerequisiteValidator(self.tree_droi2m, node_to_detach=parent_of_node_that_has_prerequisite).validate()

    def test_should_raise_exception_when_node_to_detach_is_learning_unit_that_has_prerequisite(self):
        node_having_prerequisite = self.node_has_prerequisite

        with self.assertRaises(CannotDetachLearningUnitsWhoHavePrerequisiteException):
            _HasPrerequisiteValidator(self.tree_droi2m, node_to_detach=node_having_prerequisite).validate()

    def test_should_not_raise_exception_when_node_to_detach_has_prerequisite_twice(self):
        tree = ProgramTreeFactory()
        LinkFactory(
            parent=tree.root_node,
            child=self.node_is_prerequisite,
        )
        LinkFactory(
            parent=tree.root_node,
            child=LinkFactory(
                child=self.node_has_prerequisite
            ).parent
        )  # node_has_prerequisite used once
        LinkFactory(
            parent=tree.root_node,
            child=LinkFactory(
                child=self.node_has_prerequisite
            ).parent
        )  # node_has_prerequisite used twice

        assertion = "While the prerequisite is used more than once in the same tree, we can detach it"
        self.assertValidatorNotRaises(_HasPrerequisiteValidator(tree, node_to_detach=self.node_has_prerequisite))
