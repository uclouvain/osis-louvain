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

from base.models import academic_year
from education_group.ddd.business_types import *
from education_group.ddd.domain.training import TrainingIdentity
from osis_common.ddd import interface
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.domain.service import identity_search
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository

DEFAULT_YEARS_TO_POSTPONE = 6


class CalculateEndPostponement(interface.DomainService):

    @classmethod
    def calculate_end_postponement_year_mini_training(
            cls,
            identity: 'MiniTrainingIdentity',
            repository: 'MiniTrainingRepository'
    ):
        return _calculate_end_postponement(identity, repository)

    @classmethod
    def calculate_end_postponement_year_training(
            cls,
            identity: 'TrainingIdentity',
            repository: 'TrainingRepository'
    ):
        return _calculate_end_postponement(identity, repository)

    @classmethod
    def calculate_end_postponement_year_group(
            cls,
            identity: 'GroupIdentity',
            repository: 'ProgramTreeVersionRepository'
    ):
        # Postponement for orphan groups only works if it is the root group of a program tree
        tree_identity = identity_search.ProgramTreeVersionIdentitySearch.get_from_group_identity(identity)
        return _calculate_end_postponement(tree_identity, repository)

    @classmethod
    def calculate_end_postponement_year_for_orphan_group(
            cls,
            group: 'Group',
    ):
        limit = cls.calculate_end_postponement_limit()
        if group.end_year is None:
            return limit
        return min(limit, group.end_year)

    @classmethod
    def calculate_end_postponement_year_program_tree(
            cls,
            identity: 'ProgramTreeIdentity',
            repository: 'ProgramTreeVersionRepository'
    ):
        version_identity = identity_search.ProgramTreeVersionIdentitySearch.get_from_program_tree_identity(identity)
        return cls.calculate_end_postponement_year_program_tree_version(version_identity, repository)

    @classmethod
    def calculate_end_postponement_year_program_tree_version(
            cls,
            identity: 'ProgramTreeVersionIdentity',
            repository: 'ProgramTreeVersionRepository'
    ):
        return _calculate_end_postponement(identity, repository)

    @classmethod
    def calculate_end_postponement_limit(cls) -> int:
        default_years_to_postpone = DEFAULT_YEARS_TO_POSTPONE
        current_year = academic_year.starting_academic_year().year
        return default_years_to_postpone + current_year


def _calculate_end_postponement(identity, repository) -> int:
    max_year = CalculateEndPostponement.calculate_end_postponement_limit()
    obj = repository.get(identity)
    if hasattr(obj, 'end_year_of_existence'):
        end_year = obj.end_year_of_existence
    else:
        end_year = obj.end_year
    if end_year is None:
        return max_year
    return min(max_year, end_year)
