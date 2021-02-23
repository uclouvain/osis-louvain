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
from django.test import TestCase

from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository, \
    get_fake_group_repository, get_fake_mini_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.ddd import command
from program_management.ddd.domain import program_tree_version, exception
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.service.write import delete_all_specific_versions_service
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory, \
    MandatoryRelationshipObjectFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_program_tree_version_repository
from testing.mocks import MockPatcherMixin


class TestDeleteAllProgramTreeVersions(TestCase, MockPatcherMixin):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.DeletePermanentlyTreeVersionCommand(
            acronym="ROOT",
            version_name="VERSION",
            transition_name=NOT_A_TRANSITION,
        )

    def setUp(self) -> None:
        self.fake_training_repo = get_fake_training_repository([])
        self.fake_group_repo = get_fake_group_repository([])
        self.fake_mini_training_repo = get_fake_mini_training_repository([])
        self.fake_program_tree_repo = get_fake_program_tree_repository([])
        self.fake_program_tree_version_repo = get_fake_program_tree_version_repository([])

        self.mock_repo("education_group.ddd.repository.group.GroupRepository", self.fake_group_repo)
        self.mock_repo("education_group.ddd.repository.training.TrainingRepository", self.fake_training_repo)
        self.mock_repo(
            "education_group.ddd.repository.mini_training.MiniTrainingRepository",
            self.fake_mini_training_repo
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree.ProgramTreeRepository",
            self.fake_program_tree_repo
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository",
            self.fake_program_tree_version_repo
        )
        self.tree_version_2020 = self._generate_program_tree_version(2020)
        self.tree_version_2021 = self._generate_program_tree_version(2021)

    def _generate_program_tree_version(self, year: int) -> 'program_tree_version.ProgramTreeVersion':
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[
                MandatoryRelationshipObjectFactory(
                    parent_type=TrainingType.BACHELOR,
                    child_type=GroupType.OPTION_LIST_CHOICE
                ),
                MandatoryRelationshipObjectFactory(
                    parent_type=GroupType.OPTION_LIST_CHOICE,
                    child_type=MiniTrainingType.OPTION
                )
            ]
        )
        tree = ProgramTreeFactory(
            root_node__code="LBRE",
            root_node__title="ROOT",
            root_node__year=year,
            root_node__node_type=TrainingType.BACHELOR,
            authorized_relationships=relationships
        )

        link_training_group = LinkFactory(
            parent=tree.root_node,
            child__group=True,
            child__code="LGRP",
            child__year=year,
            child__title="GROUP",
            child__node_type=GroupType.OPTION_LIST_CHOICE
        )
        link_group_minitraining = LinkFactory(
            parent=link_training_group.child,
            child__minitraining=True,
            child__code="LMIN",
            child__year=year,
            child__title="MINI",
            child__node_type=MiniTrainingType.OPTION
        )

        self.fake_training_repo.root_entities.append(
            TrainingFactory(entity_identity__acronym="ROOT", entity_identity__year=year, type=TrainingType.BACHELOR)
        )
        self.fake_group_repo.root_entities.append(
            GroupFactory(entity_identity__code="LGRP", entity_identity__year=year, type=GroupType.OPTION_LIST_CHOICE)
        )
        self.fake_mini_training_repo.root_entities.append(
            MiniTrainingFactory(entity_identity__acronym="MINI", entity_identity__year=year,
                                type=MiniTrainingType.OPTION)
        )
        self.fake_program_tree_repo.root_entities.append(tree)

        tree_version = ProgramTreeVersionFactory(
            tree=tree,
            entity_id__version_name="VERSION",
            program_tree_repository=self.fake_program_tree_repo
        )

        self.fake_program_tree_version_repo.root_entities.append(tree_version)
        return tree_version

    def test_should_return_program_tree_version_identity(self):
        result = delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)
        self.assertListEqual(
            result,
            [self.tree_version_2020.entity_id, self.tree_version_2021.entity_id]
        )

    def test_should_raise_error_when_tree_is_not_empty(self):
        LinkFactory(
            parent=self.tree_version_2020.tree.root_node,
            child__node_type=MiniTrainingType.DEEPENING
        )

        with self.assertRaises(exception.ProgramTreeNonEmpty):
            delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

    def test_should_delete_tree_version(self):
        delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

        self.assertListEqual(self.fake_program_tree_version_repo.root_entities, [])
        self.assertListEqual(self.fake_program_tree_repo.root_entities, [])

    def test_should_delete_group_objects(self):
        delete_all_specific_versions_service.delete_permanently_tree_version(self.cmd)

        self.assertListEqual(self.fake_group_repo.root_entities, [])
