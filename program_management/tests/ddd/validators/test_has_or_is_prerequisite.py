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

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from base.models.enums.education_group_types import TrainingType, GroupType
from program_management.ddd.validators._has_or_is_prerequisite import IsPrerequisiteValidator, HasPrerequisiteValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeGroupYearFactory
from program_management.tests.ddd.factories.prerequisite import cast_to_prerequisite
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestIsPrerequisiteValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        link = LinkFactory(parent__node_type=TrainingType.BACHELOR, child__node_type=GroupType.COMMON_CORE)
        self.tree = ProgramTreeFactory(root_node=link.parent)
        self.common_core = link.child
        link_with_learn_unit = LinkFactory(
            parent=self.common_core,
            child=NodeLearningUnitYearFactory(is_prerequisite_of=[])
        )
        self.node_learning_unit = link_with_learn_unit.child

    def test_should_not_raise_exception_when_children_of_node_to_detach_are_not_prerequisites(self):
        node_to_detach = self.common_core
        path_parent_of_node_to_detach = "|".join([str(self.tree.root_node.node_id)])
        LinkFactory(parent=self.common_core, child=NodeLearningUnitYearFactory(is_prerequisite_of=[]))
        LinkFactory(parent=self.common_core, child=NodeLearningUnitYearFactory(is_prerequisite_of=[]))

        validator = IsPrerequisiteValidator(self.tree, path_parent_of_node_to_detach, node_to_detach)
        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_children_of_node_to_detach_are_prerequisites(self):
        node_to_detach = self.common_core
        path_parent_of_node_to_detach = "|".join([str(self.tree.root_node.node_id)])
        link = LinkFactory(parent=self.common_core, child=NodeLearningUnitYearFactory(is_prerequisite_of=[]))
        link_with_child_that_is_prerequisite = LinkFactory(
            parent=self.common_core,
            child=NodeLearningUnitYearFactory(is_prerequisite_of=[link.child])
        )

        validator = IsPrerequisiteValidator(self.tree, path_parent_of_node_to_detach, node_to_detach)
        expected_message = _("Cannot detach education group year %(acronym)s as the following learning units "
                             "are prerequisite in %(formation)s: %(learning_units)s") % {
                               "acronym": node_to_detach.title,
                               "formation": self.tree.root_node.title,
                               "learning_units": link_with_child_that_is_prerequisite.child.code
                           }
        self.assertValidatorRaises(validator, [expected_message])

    def test_should_raise_exception_when_node_to_detach_is_prerequisite(self):
        path_parent_of_node_to_detach = "|".join([str(self.tree.root_node.node_id), str(self.common_core.node_id)])
        link_with_child_is_prerequisite = LinkFactory(
            parent=self.common_core,
            child=NodeLearningUnitYearFactory(is_prerequisite_of=[self.node_learning_unit])
        )
        node_to_detach = link_with_child_is_prerequisite.child

        validator = IsPrerequisiteValidator(self.tree, path_parent_of_node_to_detach, node_to_detach)
        expected_message = _(
            "Cannot detach learning unit %(acronym)s as it has a prerequisite or it is a prerequisite.") % {
                "acronym": node_to_detach.code
            }
        self.assertValidatorRaises(validator, [expected_message])

    def test_should_not_raise_exception_when_child_of_node_to_detach_is_prerequisite_but_reused_in_tree(self):
        #  As the node is reused somewhere else in the tree, we can detach the node without checking prerequisites
        reused_node = NodeLearningUnitYearFactory(is_prerequisite_of=[self.node_learning_unit])
        LinkFactory(parent=self.common_core, child=reused_node)
        LinkFactory(parent=self.tree.root_node, child=reused_node)

        node_to_detach = self.common_core
        path_parent_of_node_to_detach = "|".join([str(self.tree.root_node.node_id)])
        validator = IsPrerequisiteValidator(self.tree, path_parent_of_node_to_detach, node_to_detach)
        self.assertValidatorNotRaises(validator)


class TestHasPrerequisiteValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        self.node_is_prerequisite = NodeLearningUnitYearFactory()

        node_has_prerequisite = NodeLearningUnitYearFactory()
        node_has_prerequisite.set_prerequisite(cast_to_prerequisite(self.node_is_prerequisite))
        self.node_has_prerequisite = node_has_prerequisite

    def test_should_not_raise_exception_when_children_of_node_to_detach_do_not_have_prerequisites(self):
        node_to_detach = NodeGroupYearFactory()
        link = LinkFactory(child=node_to_detach)
        tree = ProgramTreeFactory(root_node=link.parent)

        validator = HasPrerequisiteValidator(tree, node_to_detach)
        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_children_of_node_to_detach_have_prerequisites(self):
        node_to_detach = NodeGroupYearFactory()

        link = LinkFactory(child=node_to_detach)
        LinkFactory(parent=node_to_detach, child=self.node_has_prerequisite)
        LinkFactory(parent=self.node_has_prerequisite, child=self.node_is_prerequisite)

        tree = ProgramTreeFactory(root_node=link.parent)

        validator = HasPrerequisiteValidator(tree, node_to_detach)
        expected_message = _("The prerequisites for the following learning units contained in education group year "
                             "%(acronym)s will we deleted: %(learning_units)s") % {
                               "acronym": tree.root_node.title,
                               "learning_units": self.node_has_prerequisite.code
                           }
        self.assertValidatorRaises(validator, [expected_message])

    def test_should_raise_exception_when_node_to_detach_is_learning_unit_that_has_prerequisite(self):
        node_to_detach_has_prerequisite = self.node_has_prerequisite

        link = LinkFactory(child=node_to_detach_has_prerequisite)

        tree = ProgramTreeFactory(root_node=link.parent)

        validator = HasPrerequisiteValidator(tree, node_to_detach_has_prerequisite)
        expected_message = _("The prerequisites for the following learning units contained in education group year "
                             "%(acronym)s will we deleted: %(learning_units)s") % {
                               "acronym": tree.root_node.title,
                               "learning_units": node_to_detach_has_prerequisite.code
                           }

        self.assertValidatorRaises(validator, [expected_message])

    def test_should_not_raise_exception_when_node_to_detach_is_learning_unit_that_has_no_prerequisite(self):
        node_to_detach_without_prerequisite = NodeLearningUnitYearFactory()

        link = LinkFactory(child=node_to_detach_without_prerequisite)

        tree = ProgramTreeFactory(root_node=link.parent)

        validator = HasPrerequisiteValidator(tree, node_to_detach_without_prerequisite)
        self.assertValidatorNotRaises(validator)
