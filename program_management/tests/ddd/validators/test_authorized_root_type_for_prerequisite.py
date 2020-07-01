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
from django.test import SimpleTestCase

from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class TestAuthorizedRootTypeForPrerequisite(SimpleTestCase):
    def test_is_valid_should_return_false_when_root_type_is_group(self):
        root_node = NodeGroupYearFactory(group=True)
        validator = AuthorizedRootTypeForPrerequisite(root_node)
        self.assertFalse(validator.is_valid())

    def test_is_valid_should_return_false_when_root_type_is_option_or_mobility_partnership(self):
        not_authorized_types = (MiniTrainingType.OPTION, MiniTrainingType.MOBILITY_PARTNERSHIP)
        for node_type in not_authorized_types:
            with self.subTest(type=node_type):
                root_node = NodeGroupYearFactory(node_type=node_type)
                validator = AuthorizedRootTypeForPrerequisite(root_node)
                self.assertFalse(validator.is_valid())

    def test_is_valid_should_return_false_when_root_type_is_a_finality(self):
        not_authorized_types = TrainingType.finality_types_enum()
        for node_type in not_authorized_types:
            with self.subTest(type=node_type):
                root_node = NodeGroupYearFactory(node_type=node_type)
                validator = AuthorizedRootTypeForPrerequisite(root_node)
                self.assertFalse(validator.is_valid())

    def test_is_valid_should_return_true_when_root_type_is_of_other_type(self):
        authorized_types = (set(MiniTrainingType) | set(TrainingType)) - set(TrainingType.finality_types_enum()) \
                           - set((MiniTrainingType.OPTION, MiniTrainingType.MOBILITY_PARTNERSHIP))
        for node_type in authorized_types:
            with self.subTest(type=node_type):
                root_node = NodeGroupYearFactory(node_type=node_type)
                validator = AuthorizedRootTypeForPrerequisite(root_node)
                self.assertTrue(validator.is_valid())
