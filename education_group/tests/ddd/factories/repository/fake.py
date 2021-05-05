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
from typing import List, Type, Optional

from education_group.ddd.business_types import *
from education_group.ddd.domain import exception
from education_group.ddd.repository import group as group_repository, mini_training as mini_training_repository, \
    training as training_repository


#  TODO update and get should work on copy
class FakeGroupRepository(group_repository.GroupRepository):
    _groups = list()  # type: List['Group']

    @classmethod
    def create(cls, group: 'Group', **_) -> 'GroupIdentity':
        cls._groups.append(group)
        from program_management.tests.ddd.factories import node as node_factory
        node_factory.NodeGroupYearFactory.from_group(group, persist=True)
        return group.entity_id

    @classmethod
    def update(cls, group: 'Group', **_) -> 'GroupIdentity':
        if group not in cls._groups:
            raise exception.GroupNotFoundException()
        return group.entity_id

    @classmethod
    def get(cls, entity_id: 'GroupIdentity') -> 'Group':
        result = next((group for group in cls._groups if group.entity_id == entity_id), None)
        if not result:
            raise exception.GroupNotFoundException()
        return result

    @classmethod
    def search(cls, entity_ids: Optional[List['GroupIdentity']] = None, code=None, **kwargs) -> List['Group']:
        if entity_ids:
            return [group for group in cls._groups if group.entity_id in entity_ids]
        if code:
            return [group for group in cls._groups if group.entity_id.code == code]
        return []

    @classmethod
    def delete(cls, entity_id: 'GroupIdentity', **_) -> None:
        group_to_delete = next((group for group in cls._groups if group.entity_id == entity_id), None)
        if group_to_delete:
            cls._groups.remove(group_to_delete)


#  TODO update and get should work on copy
class FakeMiniTrainingRepository(mini_training_repository.MiniTrainingRepository):
    _mini_trainings = list()  # type: List['MiniTraining']

    @classmethod
    def create(cls, mini_training: 'MiniTraining', **_) -> 'MiniTrainingIdentity':
        cls._mini_trainings.append(mini_training)
        return mini_training.entity_id

    @classmethod
    def update(cls, mini_training: 'MiniTraining', **_) -> 'MiniTrainingIdentity':
        if mini_training not in cls._mini_trainings:
            raise exception.MiniTrainingNotFoundException()
        return mini_training.entity_id

    @classmethod
    def get(cls, entity_id: 'MiniTrainingIdentity') -> 'MiniTraining':
        result = next(
            (mini_training for mini_training in cls._mini_trainings if mini_training.entity_id == entity_id),
            None
        )
        if not result:
            raise exception.MiniTrainingNotFoundException()
        return result

    @classmethod
    def search(cls, entity_ids: Optional[List['MiniTrainingIdentity']] = None, **kwargs) -> List['MiniTraining']:
        if entity_ids:
            return [mini_training for mini_training in cls._mini_trainings if mini_training.entity_id in entity_ids]
        return []

    @classmethod
    def delete(cls, entity_id: 'MiniTrainingIdentity', **_) -> None:
        mini_training_to_delete = next(
            (mini_training for mini_training in cls._mini_trainings if mini_training.entity_id == entity_id),
            None
        )
        if mini_training_to_delete:
            cls._mini_trainings.remove(mini_training_to_delete)


#  TODO update and get should work on copy
class FakeTrainingRepository(training_repository.TrainingRepository):
    _trainings = list()  # type: List['Training']

    @classmethod
    def create(cls, training: 'Training', **_) -> 'TrainingIdentity':
        cls._trainings.append(training)
        return training.entity_id

    @classmethod
    def update(cls, training: 'Training', **_) -> 'TrainingIdentity':
        if training not in cls._trainings:
            raise exception.TrainingNotFoundException()
        return training.entity_id

    @classmethod
    def get(cls, entity_id: 'TrainingIdentity') -> 'Training':
        result = next(
            (training for training in cls._trainings if training.entity_id == entity_id),
            None
        )
        if not result:
            raise exception.TrainingNotFoundException()
        return result

    @classmethod
    def search(cls, entity_ids: Optional[List['TrainingIdentity']] = None, **kwargs) -> List['Training']:
        if entity_ids:
            return [training for training in cls._trainings if training.entity_id in entity_ids]
        return []

    @classmethod
    def delete(cls, entity_id: 'TrainingIdentity', **_) -> None:
        training_to_delete = next((training for training in cls._trainings if training.entity_id == entity_id), None)
        if training_to_delete:
            cls._trainings.remove(training_to_delete)


def get_fake_group_repository(root_entities: List['Group']) -> Type['FakeGroupRepository']:
    FakeGroupRepository._groups = root_entities
    return FakeGroupRepository


def get_fake_mini_training_repository(root_entities: List['MiniTraining']) -> Type['FakeMiniTrainingRepository']:
    FakeMiniTrainingRepository._mini_trainings = root_entities
    return FakeMiniTrainingRepository


def get_fake_training_repository(root_entities: List['Training']) -> Type['FakeTrainingRepository']:
    FakeTrainingRepository._trainings = root_entities
    return FakeTrainingRepository
