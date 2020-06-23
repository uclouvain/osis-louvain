# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from unittest.mock import Mock

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from base.ddd.utils.validation_message import MessageLevel
from base.models.enums.education_group_types import TrainingType
from program_management.ddd.validators import _validate_end_date_and_option_finality
from program_management.ddd.validators._attach_finality_end_date import AttachFinalityEndDateValidator
from program_management.ddd.validators._attach_option import AttachOptionsValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestValidateEndDateAndOptionFinality(TestValidatorValidateMixin, ValidatorPatcherMixin, SimpleTestCase):

    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_type=TrainingType.PGRM_MASTER_120)
        self.tree_2m = ProgramTreeFactory(root_node=self.root_node)
        self.root_path = str(self.root_node.node_id)
        self.node_to_attach_not_finality = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)

        self.mock_repository = self._mock_repository()

    def _mock_repository(self):
        mock = Mock()
        attrs = {
            "get.return_value": ProgramTreeFactory(root_node=self.node_to_attach_not_finality)
        }
        mock.configure_mock(**attrs)
        return mock

    def test_should_not_raise_exception_when_node_to_attach_is_not_finality(self):
        """Unit test only for performance"""
        self.mock_validator(AttachFinalityEndDateValidator, ['Success message'], level=MessageLevel.SUCCESS)

        self.assertValidatorNotRaises(
            _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(
                self.node_to_attach_not_finality,
                self.mock_repository
            )
        )
        self.assertFalse(self.mock_repository.search_from_children.called)

    def test_should_raise_exception_when_end_date_of_finality_node_to_attach_is_not_valid(self):
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        attrs = {
            "search_from_children.return_value": [self.tree_2m],
            "get.return_value": ProgramTreeFactory(root_node=node_to_attach)
        }
        self.mock_repository.configure_mock(**attrs)
        self.mock_validator(AttachFinalityEndDateValidator, ['Error end date finality message'])

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(
                node_to_attach,
                self.mock_repository
            ),
            ['Error end date finality message']
        )

    def test_should_raise_exception_when_end_date_of_finality_children_of_node_to_attach_is_not_valid(self):
        not_finality = NodeGroupYearFactory(node_type=TrainingType.AGGREGATION)
        finality = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        not_finality.add_child(finality)
        attrs = {
            "search_from_children.return_value": [self.tree_2m],
            "get.return_value": ProgramTreeFactory(root_node=not_finality)
        }
        self.mock_repository.configure_mock(**attrs)
        self.mock_validator(AttachFinalityEndDateValidator, ['Error end date finality message'])

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(not_finality, self.mock_repository),
            ['Error end date finality message']
        )

    def test_should_not_raise_exception_when_end_date_of_finality_node_to_attach_is_valid(self):
        finality = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        attrs = {
            "search_from_children.return_value": [self.tree_2m],
            "get.return_value": ProgramTreeFactory(root_node=finality)
        }
        self.mock_repository.configure_mock(**attrs)
        self.mock_validator(AttachFinalityEndDateValidator, [_('Success')], level=MessageLevel.SUCCESS)

        self.assertValidatorNotRaises(
            _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(finality, self.mock_repository)
        )

    def test_should_raise_exception_when_option_validator_not_valid(self):
        node_to_attach = NodeGroupYearFactory(node_type=TrainingType.MASTER_MA_120)
        attrs = {
            "search_from_children.return_value": [self.tree_2m],
            "get.return_value": ProgramTreeFactory(root_node=node_to_attach)
        }
        self.mock_repository.configure_mock(**attrs)
        self.mock_validator(AttachOptionsValidator, ['Error attach option message'])

        self.assertValidatorRaises(
            _validate_end_date_and_option_finality.ValidateEndDateAndOptionFinality(
                node_to_attach,
                self.mock_repository
            ),
            None
        )
