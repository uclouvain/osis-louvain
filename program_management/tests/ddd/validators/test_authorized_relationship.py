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

from base.models.authorized_relationship import AuthorizedRelationshipList
from base.models.enums.education_group_types import TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.domain.exception import MinimumChildTypesNotRespectedException
from program_management.ddd.validators._authorized_relationship import DetachAuthorizedRelationshipValidator
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestDetachAuthorizedRelationshipValidator(TestValidatorValidateMixin, SimpleTestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory.build(current=True)

        self.authorized_parent = NodeGroupYearFactory(
            node_type=TrainingType.BACHELOR,
            year=self.academic_year.year,
        )
        self.authorized_child = NodeGroupYearFactory(
            node_type=GroupType.COMMON_CORE,
            year=self.academic_year.year,
        )
        self.authorized_relationships = AuthorizedRelationshipList([
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_parent.node_type,
                child_type=self.authorized_child.node_type,
                min_count_authorized=1,
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_child.node_type,
                child_type=GroupType.SUB_GROUP,
                min_count_authorized=1,
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=self.authorized_child.node_type,
                child_type=NodeType.LEARNING_UNIT,
                min_count_authorized=0,
            ),
        ])
        self.tree = ProgramTreeFactory(
            root_node=self.authorized_parent,
            authorized_relationships=self.authorized_relationships
        )

    def test_should_not_raise_exception_when_relation_is_not_authorized(self):
        """
            Business case to fix :
            MINOR_LIST_CHOICE
               |--ACCESS_MINOR (link_type=reference)
                  |--COMMON_CORE
            # FIXME :: What if we want to detach ACCESS_MINOR in the tree above?
            # FIXME :: In this case, the relation between child of minor () COMMON_CORE
            #          and parent of minor (MINOR_LIST_CHOICE) is not authorized.
            # FIXME :: While this test pass, it permit to ignore validation if the authorized_relationship
            #          does not exist.
        """
        unauthorized_child = NodeGroupYearFactory(node_type=GroupType.COMPLEMENTARY_MODULE)
        LinkFactory(parent=self.authorized_parent, child=unauthorized_child)
        validator = DetachAuthorizedRelationshipValidator(self.tree, unauthorized_child, self.authorized_parent)
        self.assertValidatorNotRaises(validator)

    def test_should_not_raise_exception_when_minimum_is_not_reached_when_detaching(self):
        another_authorized_child = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        another_authorized_parent = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        another_authorized_parent.add_child(another_authorized_child)
        another_authorized_parent.add_child(self.authorized_child)
        tree = ProgramTreeFactory(
            root_node=another_authorized_parent,
            authorized_relationships=self.authorized_relationships
        )
        validator = DetachAuthorizedRelationshipValidator(tree, another_authorized_child, another_authorized_parent)
        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_minimum_is_reached_when_detaching(self):
        node_to_detach = self.authorized_child
        detach_from = self.authorized_parent
        LinkFactory(parent=detach_from, child=node_to_detach)
        with self.assertRaises(MinimumChildTypesNotRespectedException):
            DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from).validate()

    def test_should_not_raise_exception_when_link_to_detach_is_learning_unit(self):
        """
        BACHELOR
           |--COMMON_CORE
              |--LEARNING_UNIT
        """
        LinkFactory(parent=self.authorized_parent, child=self.authorized_child)
        link = LinkFactory(parent=self.authorized_child, child__node_type=NodeType.LEARNING_UNIT)

        node_to_detach = link.child
        detach_from = link.parent
        validator = DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from)

        self.assertValidatorNotRaises(validator)

    def test_should_raise_exception_when_node_to_detach_is_linked_by_reference_and_min_reached_for_its_children(self):
        LinkFactory(parent=self.authorized_parent, child=self.authorized_child)
        reference_link = LinkFactory(
            parent=self.authorized_child,
            child__node_type=self.authorized_child.node_type,
            link_type=LinkTypes.REFERENCE
        )
        child_type_under_reference = GroupType.SUB_GROUP
        LinkFactory(parent=reference_link.child, child__node_type=child_type_under_reference)

        node_to_detach = reference_link.child
        detach_from = reference_link.parent
        with self.assertRaises(MinimumChildTypesNotRespectedException):
            DetachAuthorizedRelationshipValidator(self.tree, node_to_detach, detach_from).validate()
