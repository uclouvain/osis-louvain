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

from base.models.enums import education_group_types
from education_group.ddd.domain import exception as education_group_exception
from education_group.ddd.domain import training, group, mini_training
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.tests.ddd.factories.repository.fake import get_fake_training_repository, \
    get_fake_group_repository, \
    get_fake_mini_training_repository
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.ddd import command
from program_management.ddd.domain import program_tree, exception
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.service.write import delete_standard_program_tree_version_service
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory, \
    MandatoryRelationshipObjectFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_program_tree_version_repository
from testing.mocks import MockPatcherMixin


class TestDeleteStandardProgramTreeService(TestCase, MockPatcherMixin):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = command.DeleteProgramTreeVersionCommand(
            offer_acronym="ROOT",
            from_year=2018,
            transition_name=NOT_A_TRANSITION,
            version_name=""
        )

    def setUp(self):
        self.trainings = [
            TrainingFactory(entity_identity__acronym="ROOT", entity_identity__year=year,
                            type=education_group_types.TrainingType.BACHELOR)
            for year in range(2018, 2020)
        ]
        self.fake_training_repo = get_fake_training_repository(self.trainings)

        self.groups = [
            GroupFactory(entity_identity__code="GROUP", entity_identity__year=year,
                         type=education_group_types.GroupType.OPTION_LIST_CHOICE)
            for year in range(2018, 2020)
        ]
        self.fake_group_repo = get_fake_group_repository(self.groups)

        self.mini_trainings = [
            MiniTrainingFactory(entity_identity__acronym="CHILD", entity_identity__year=year,
                                type=education_group_types.MiniTrainingType.OPTION)
            for year in range(2018, 2020)
        ]
        self.fake_mini_training_repo = get_fake_mini_training_repository(self.mini_trainings)

        self.program_trees = [
            self._generate_program_tree(training_obj, group_obj, mini_obj)
            for training_obj, group_obj, mini_obj in zip(self.trainings, self.groups, self.mini_trainings)
        ]
        self.fake_program_tree_repo = get_fake_program_tree_repository(self.program_trees)

        self.program_tree_versions = [
            ProgramTreeVersionFactory(
                tree=tree,
                program_tree_repository=self.fake_program_tree_repo,
                entity_id__version_name=self.cmd.version_name
            )
            for tree in self.program_trees
        ]
        self.fake_program_tree_version_repo = get_fake_program_tree_version_repository(self.program_tree_versions)

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

    def _generate_program_tree(
            self,
            training_obj: 'training.Training',
            group_obj: 'group.Group',
            mini_training_obj: 'mini_training.MiniTraining') -> 'program_tree.ProgramTree':
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[
                MandatoryRelationshipObjectFactory(parent_type=training_obj.type, child_type=group_obj.type),
                MandatoryRelationshipObjectFactory(parent_type=group_obj.type, child_type=mini_training_obj.type)
            ]
        )
        tree = ProgramTreeFactory(
            root_node__code=training_obj.code,
            root_node__title=training_obj.acronym,
            root_node__year=training_obj.year,
            root_node__node_type=training_obj.type,
            authorized_relationships=relationships
        )
        link_training_group = LinkFactory(
            parent=tree.root_node,
            child__group=True,
            child__code=group_obj.code,
            child__year=group_obj.year,
            child__title=group_obj.abbreviated_title,
            child__node_type=group_obj.type
        )
        link_group_minitraining = LinkFactory(
            parent=link_training_group.child,
            child__minitraining=True,
            child__code=mini_training_obj.code,
            child__year=mini_training_obj.year,
            child__title=mini_training_obj.acronym,
            child__node_type=mini_training_obj.type
        )
        return tree

    def test_should_return_program_tree_version_identities(self):
        result = delete_standard_program_tree_version_service.delete_standard_program_tree_version(self.cmd)
        expected_result = [tree_version.entity_id for tree_version in self.program_tree_versions]

        self.assertListEqual(expected_result, result)

    def test_should_delete_program_tree_versions(self):
        tree_version_identities = delete_standard_program_tree_version_service.delete_standard_program_tree_version(
            self.cmd
        )
        for identity in tree_version_identities:
            with self.assertRaises(exception.ProgramTreeVersionNotFoundException):
                self.fake_program_tree_version_repo.get(identity)

    def test_should_delete_program_trees(self):
        delete_standard_program_tree_version_service.delete_standard_program_tree_version(self.cmd)

        program_tree_identities = [tree.entity_id for tree in self.program_trees]
        for identity in program_tree_identities:
            with self.assertRaises(exception.ProgramTreeNotFoundException):
                self.fake_program_tree_repo.get(identity)

    def test_should_delete_groups(self):
        delete_standard_program_tree_version_service.delete_standard_program_tree_version(self.cmd)

        group_identities = [obj.entity_id for obj in self.groups]
        for identity in group_identities:
            with self.assertRaises(education_group_exception.GroupNotFoundException):
                self.fake_group_repo.get(identity)
