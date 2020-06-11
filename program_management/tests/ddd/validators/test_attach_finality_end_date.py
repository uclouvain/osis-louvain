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

from base.models.enums.education_group_types import TrainingType
from program_management.ddd.validators._attach_finality_end_date import AttachFinalityEndDateValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestAttachFinalityEndDateValidator(SimpleTestCase):

    def setUp(self):
        self.tree_2m = ProgramTreeFactory(
            root_node__node_type=TrainingType.PGRM_MASTER_120,
            root_node__end_date=2099
        )

        self.finality_node_greater_end_date = NodeGroupYearFactory(
            node_type=TrainingType.MASTER_MA_120,
            end_date=self.tree_2m.root_node.end_date + 1
        )

    def test_init_when_tree_is_not_2m_and_node_to_attach_has_no_finality(self):
        not_tree_2m = ProgramTreeFactory(root_node__node_type=TrainingType.BACHELOR)
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.ACCESS_CONTEST)
        validator = AttachFinalityEndDateValidator(not_tree_2m, ProgramTreeFactory(root_node=node_to_attach))
        self.assertTrue(validator.is_valid())

    def test_init_when_tree_is_not_2m_and_node_to_attach_has_finality(self):
        not_tree_2m = ProgramTreeFactory(root_node__node_type=TrainingType.BACHELOR)
        with self.assertRaises(AssertionError):
            node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
            AttachFinalityEndDateValidator(not_tree_2m, ProgramTreeFactory(root_node=node_to_attach))

    def test_when_node_to_attach_is_finality_and_end_date_greater_than_2m(self):
        validator = AttachFinalityEndDateValidator(
            self.tree_2m,
            ProgramTreeFactory(root_node=self.finality_node_greater_end_date)
        )
        self.assertFalse(validator.is_valid())
        expected_msg = ngettext(
            "Finality \"%(code)s\" has an end date greater than %(root_code)s program.",
            "Finalities \"%(code)s\" have an end date greater than %(root_code)s program.",
            1
        ) % {
            'code': self.finality_node_greater_end_date.code,
            'root_code': self.tree_2m.root_node.code
        }
        self.assertEqual(expected_msg, validator.error_messages[0])

    def test_when_node_to_attach_is_finality_and_end_date_lower(self):
        finality_node = NodeGroupYearFactory(
            node_type=TrainingType.MASTER_MA_120,
            end_date=self.tree_2m.root_node.end_date - 1
        )
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=finality_node))
        self.assertTrue(validator.is_valid())

    def test_when_node_to_attach_is_finality_and_end_date_equals(self):
        finality_node = NodeGroupYearFactory(
            node_type=TrainingType.MASTER_MA_120,
            end_date=self.tree_2m.root_node.end_date
        )
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=finality_node))
        self.assertTrue(validator.is_valid())

    def test_when_node_to_attach_contains_finality_and_end_date_greater(self):
        node_to_attach = NodeGroupYearFactory()
        node_to_attach.add_child(self.finality_node_greater_end_date)
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=node_to_attach))
        self.assertFalse(validator.is_valid())
        expected_msg = ngettext(
            "Finality \"%(code)s\" has an end date greater than %(root_code)s program.",
            "Finalities \"%(code)s\" have an end date greater than %(root_code)s program.",
            1
        ) % {
           'code': self.finality_node_greater_end_date.code,
           'root_code': self.tree_2m.root_node.code
        }
        self.assertEqual(expected_msg, validator.error_messages[0])

    def test_when_node_to_attach_contains_finality_and_end_date_equals(self):
        node_to_attach = NodeGroupYearFactory(end_date=self.tree_2m.root_node.end_date)
        finality_node = NodeGroupYearFactory(
            node_type=TrainingType.MASTER_MA_120,
            end_date=self.tree_2m.root_node.end_date
        )
        node_to_attach.add_child(finality_node)
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=node_to_attach))
        self.assertTrue(validator.is_valid())

    def test_validate_when_node_to_attach_is_not_finality(self):
        not_finality_node = NodeGroupYearFactory(
            node_type=TrainingType.ACCESS_CONTEST,
            end_date=self.tree_2m.root_node.end_date + 1
        )
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=not_finality_node))
        self.assertTrue(validator.is_valid())

    def test_validate_when_node_to_attach_has_no_finality(self):
        node_to_attach = NodeGroupYearFactory()
        not_finality_node = NodeGroupYearFactory(
            node_type=TrainingType.MASTER_MA_120,
            end_date=self.tree_2m.root_node.end_date
        )
        node_to_attach.add_child(not_finality_node)
        validator = AttachFinalityEndDateValidator(self.tree_2m, ProgramTreeFactory(root_node=node_to_attach))
        test = validator.is_valid()
        self.assertTrue(test)
