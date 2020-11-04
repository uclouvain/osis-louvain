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

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from program_management.ddd.domain.exception import ProgramTreeVersionMismatch
from program_management.ddd.validators._match_version import MatchVersionValidator
from program_management.tests.ddd.factories.program_tree import tree_builder
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory, \
    SpecificProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_program_tree_version_repository
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestMatchVersionValidator(TestValidatorValidateMixin, SimpleTestCase):
    def setUp(self):
        tree_data = {
            "node_type": TrainingType.PGRM_MASTER_120,
            "end_year": 2019,
            "children": [
                {
                    "node_type": GroupType.FINALITY_120_LIST_CHOICE
                },
                {
                    "node_type": GroupType.OPTION_LIST_CHOICE,
                    "children": [
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTA", "year": 2019},
                        {"node_type": MiniTrainingType.OPTION, "code": "OPTB", "year": 2019}
                    ]
                }
            ]
        }
        self.tree = tree_builder(tree_data)
        self.tree_version = StandardProgramTreeVersionFactory(tree=self.tree)

    def test_should_not_raise_exception_when_versions_match(self):
        tree_to_attach = tree_builder({"node_type": TrainingType.MASTER_MA_120, "end_year": 2019})
        tree_to_attach_version = StandardProgramTreeVersionFactory(tree=tree_to_attach)

        fake_program_tree_repository = get_fake_program_tree_repository([self.tree, tree_to_attach])
        fake_tree_version_repository = get_fake_program_tree_version_repository([
            self.tree_version, tree_to_attach_version
        ])

        self.assertValidatorNotRaises(
            MatchVersionValidator(
                node_to_paste_to=self.tree.root_node,
                node_to_add=tree_to_attach.root_node,
                tree_repository=fake_program_tree_repository,
                tree_version_repository=fake_tree_version_repository
            )
        )

    def test_should_raise_exception_when_versions_mismatch(self):
        tree_to_attach = tree_builder(
            {"node_type": TrainingType.MASTER_MA_120, "version_name": "SPECIFIC", "end_year": 2019}
        )
        tree_to_attach_version = SpecificProgramTreeVersionFactory(tree=tree_to_attach)

        fake_program_tree_repository = get_fake_program_tree_repository([self.tree, tree_to_attach])
        fake_tree_version_repository = get_fake_program_tree_version_repository([
            self.tree_version, tree_to_attach_version
        ])

        with self.assertRaises(ProgramTreeVersionMismatch):
            MatchVersionValidator(
                node_to_paste_to=self.tree.root_node,
                node_to_add=tree_to_attach.root_node,
                tree_repository=fake_program_tree_repository,
                tree_version_repository=fake_tree_version_repository
            ).validate()

    def test_should_raise_exception_when_children_version_mismatch(self):
        tree_to_attach = tree_builder(
            {
                "node_type": GroupType.FINALITY_120_LIST_CHOICE,
                "end_year": 2019,
                "children": [{"node_type": TrainingType.MASTER_MA_120, "version_name": "SPECIFIC", "end_year": 2019}]
            }
        )
        tree_to_attach_version = SpecificProgramTreeVersionFactory(tree=tree_to_attach)

        fake_program_tree_repository = get_fake_program_tree_repository([self.tree, tree_to_attach])
        fake_tree_version_repository = get_fake_program_tree_version_repository([
            self.tree_version, tree_to_attach_version
        ])

        with self.assertRaises(ProgramTreeVersionMismatch):
            MatchVersionValidator(
                node_to_paste_to=self.tree.root_node,
                node_to_add=tree_to_attach.root_node,
                tree_repository=fake_program_tree_repository,
                tree_version_repository=fake_tree_version_repository
            ).validate()

    def test_should_not_raise_exception_when_minitraining_version_mismatch(self):
        tree_to_attach = tree_builder(
            {"node_type": MiniTrainingType.OPEN_MINOR, "version_name": "SPECIFIC", "end_year": 2019}
        )
        tree_to_attach_version = SpecificProgramTreeVersionFactory(tree=tree_to_attach)

        fake_program_tree_repository = get_fake_program_tree_repository([self.tree, tree_to_attach])
        fake_tree_version_repository = get_fake_program_tree_version_repository([
            self.tree_version, tree_to_attach_version
        ])
        self.assertValidatorNotRaises(
            MatchVersionValidator(
                node_to_paste_to=self.tree.root_node,
                node_to_add=tree_to_attach.root_node,
                tree_repository=fake_program_tree_repository,
                tree_version_repository=fake_tree_version_repository
            )
        )
