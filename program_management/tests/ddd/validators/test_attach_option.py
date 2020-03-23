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
from django.utils.translation import ngettext

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from program_management.ddd.validators._attach_option import AttachOptionsValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestAttachOptionsValidator(SimpleTestCase):

    def setUp(self):
        self.option = NodeGroupYearFactory(node_type=MiniTrainingType.OPTION)
        link_2m_list_option = LinkFactory(
            parent__node_type=TrainingType.PGRM_MASTER_120,
            child__node_type=GroupType.OPTION_LIST_CHOICE,
        )
        LinkFactory(
            parent=link_2m_list_option.child,
            child=self.option,
        )
        self.tree_2m_with_option = ProgramTreeFactory(
            root_node=link_2m_list_option.parent,
        )

        link_finality_list_option = LinkFactory(
            parent__node_type=TrainingType.MASTER_MA_120,
            child__node_type=GroupType.OPTION_LIST_CHOICE,
        )
        self.link_option_list_option = LinkFactory(
            parent=link_finality_list_option.child,
            child=self.option,
        )
        self.finality_list_option = link_finality_list_option.child
        self.finality_node_with_option = link_finality_list_option.parent

    def test_init_when_tree_is_not_2m_and_node_to_attach_has_no_finality(self):
        not_tree_2m = ProgramTreeFactory(root_node__node_type=TrainingType.BACHELOR)
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.ACCESS_CONTEST)
        validator = AttachOptionsValidator(not_tree_2m, ProgramTreeFactory(root_node=node_to_attach))
        self.assertTrue(validator.is_valid())

    def test_init_when_tree_is_not_2m_and_node_to_attach_has_finality(self):
        not_tree_2m = ProgramTreeFactory(root_node__node_type=TrainingType.BACHELOR)
        with self.assertRaises(AssertionError):
            node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
            AttachOptionsValidator(not_tree_2m, ProgramTreeFactory(root_node=node_to_attach))

    def test_when_node_to_attach_is_finality_and_options_differs_from_2m(self):
        different_option = NodeGroupYearFactory(node_type=MiniTrainingType.OPTION)
        self.finality_list_option.add_child(different_option)
        validator = AttachOptionsValidator(
            self.tree_2m_with_option,
            ProgramTreeFactory(root_node=self.finality_node_with_option)
        )
        self.assertFalse(validator.is_valid())
        expected_result = ngettext(
            "Option \"%(acronym)s\" must be present in %(root_acronym)s program.",
            "Options \"%(acronym)s\" must be present in %(root_acronym)s program.",
            1
        ) % {
            'acronym': different_option.acronym,
            'root_acronym': self.tree_2m_with_option.root_node.acronym,
        }
        self.assertEqual(expected_result, validator.error_messages[0].message)

    def test_when_node_to_attach_is_finality_and_options_exist_in_2m(self):
        validator = AttachOptionsValidator(
            self.tree_2m_with_option,
            ProgramTreeFactory(root_node=self.finality_node_with_option)
        )
        self.assertTrue(validator.is_valid())

    def test_when_node_to_attach_has_finality_and_options_differs_from_2m(self):
        different_option = NodeGroupYearFactory(node_type=MiniTrainingType.OPTION)
        self.finality_list_option.add_child(different_option)
        link = LinkFactory(child=self.finality_node_with_option)
        validator = AttachOptionsValidator(
            self.tree_2m_with_option,
            ProgramTreeFactory(root_node=link.parent)
        )
        self.assertFalse(validator.is_valid())
        expected_result = ngettext(
            "Option \"%(acronym)s\" must be present in %(root_acronym)s program.",
            "Options \"%(acronym)s\" must be present in %(root_acronym)s program.",
            1
        ) % {
            'acronym': different_option.acronym,
            'root_acronym': self.tree_2m_with_option.root_node.acronym,
        }
        self.assertEqual(expected_result, validator.error_messages[0].message)

    def test_when_node_to_attach_has_finality_and_options_exist_in_2m(self):
        validator = AttachOptionsValidator(
            self.tree_2m_with_option,
            ProgramTreeFactory(root_node=self.finality_list_option)
        )
        self.assertTrue(validator.is_valid())

