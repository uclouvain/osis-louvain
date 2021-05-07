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
import collections
import itertools
from typing import Dict, List

import attr

from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from education_group.ddd.domain.exception import GroupNotFoundException, TrainingNotFoundException, \
    MiniTrainingNotFoundException
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.repository.group import GroupRepository
from education_group.ddd.repository.mini_training import MiniTrainingRepository
from education_group.ddd.repository.training import TrainingRepository
from osis_common.ddd import interface
from program_management.ddd.domain.link import Link
from program_management.ddd.domain.program_tree import ProgramTreeIdentity, ProgramTree
from program_management.ddd.domain.service.search_program_trees_in_future import SearchProgramTreesInFuture
from program_management.ddd.repositories.program_tree import ProgramTreeRepository

Year = int
FieldLabel = str


class ConflictedFields(interface.DomainService):
    @classmethod
    def get_group_conflicted_fields(cls, group_id: 'GroupIdentity') -> Dict[Year, List[FieldLabel]]:
        current_group = GroupRepository.get(group_id)
        conflicted_fields = {}

        for year in itertools.count(current_group.year + 1):
            try:
                next_year_group_identity = attr.evolve(current_group.entity_id, year=current_group.entity_id.year + 1)
                next_year_group = GroupRepository.get(next_year_group_identity)
                if not current_group.has_same_values_as(next_year_group):
                    conflicted_fields[year] = current_group.get_conflicted_fields(next_year_group)
            except GroupNotFoundException:
                break
            current_group = next_year_group
        return conflicted_fields

    @classmethod
    def get_training_conflicted_fields(cls, training_id: 'TrainingIdentity') -> Dict[Year, List[FieldLabel]]:
        current_training = TrainingRepository.get(training_id)
        group_id = GroupIdentity(code=current_training.code, year=current_training.year)
        conflicted_fields = collections.defaultdict(list)
        conflicted_fields.update(cls.get_group_conflicted_fields(group_id))

        for year in itertools.count(current_training.year + 1):
            try:
                next_year_training_identity = attr.evolve(
                    current_training.entity_id,
                    year=current_training.entity_id.year + 1
                )
                next_year_training = TrainingRepository.get(next_year_training_identity)
                if not current_training.has_same_values_as(next_year_training):
                    conflicted_fields[year].extend(current_training.get_conflicted_fields(next_year_training))
            except TrainingNotFoundException:
                break
            current_training = next_year_training
        return conflicted_fields

    @classmethod
    def get_mini_training_conflicted_fields(cls, mini_training_id: 'MiniTrainingIdentity') \
            -> Dict[Year, List[FieldLabel]]:
        current_mini_training = MiniTrainingRepository.get(mini_training_id)
        group_id = GroupIdentity(code=current_mini_training.code, year=current_mini_training.year)
        conflicted_fields = collections.defaultdict(list)
        conflicted_fields.update(cls.get_group_conflicted_fields(group_id))

        for year in itertools.count(current_mini_training.year + 1):
            try:
                next_year_mini_training_identity = attr.evolve(
                    current_mini_training.entity_id,
                    year=current_mini_training.entity_id.year + 1
                )
                next_year_mini_training = MiniTrainingRepository.get(next_year_mini_training_identity)
                if not current_mini_training.has_same_values_as(next_year_mini_training):
                    conflicted_fields[year].extend(current_mini_training.get_conflicted_fields(next_year_mini_training))
            except MiniTrainingNotFoundException:
                break
            current_mini_training = next_year_mini_training
        return conflicted_fields

    @classmethod
    def get_conflicted_certificate_aims(cls, training_id: 'TrainingIdentity') -> List[Year]:
        current_training = TrainingRepository.get(training_id)
        conflicted_aims = []

        for year in itertools.count(current_training.year + 1):
            try:
                next_year_training_identity = attr.evolve(
                    current_training.entity_id,
                    year=current_training.entity_id.year + 1
                )
                next_year_training = TrainingRepository.get(next_year_training_identity)
                if current_training.has_conflicted_certificate_aims(next_year_training):
                    conflicted_aims.append(year)
            except TrainingNotFoundException:
                break
            current_training = next_year_training
        return conflicted_aims

    @classmethod
    def get_conflicted_links(
            cls,
            updated_link: 'Link',
            ordered_trees_in_future: List['ProgramTree']
    ) -> Dict[Year, List[FieldLabel]]:
        conflicted_fields = {}
        current_link = updated_link
        for next_year_tree in ordered_trees_in_future:
            next_year_link_identity = current_link.entity_id.get_next_year_link_identity()
            next_year_link = next_year_tree.get_link_from_identity(next_year_link_identity)
            if not current_link.has_same_values_as(next_year_link):
                conflicted_fields[next_year_tree.year] = current_link.get_conflicted_fields(next_year_link)
            current_link = next_year_link
        return conflicted_fields
