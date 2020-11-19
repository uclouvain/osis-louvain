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
from typing import List, Set

from base.ddd.utils import business_validator
from base.models.enums.education_group_types import TrainingType
from base.utils.constants import INFINITE_VALUE
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import FinalitiesEndDateGreaterThanTheirMasters2MException, \
    Program2MEndDateLowerThanItsFinalitiesException


class CheckEndDateBetweenFinalitiesAndMasters2M(business_validator.BusinessValidator):
    """
    In context of 2M, when we add a finality [or group which contains finality], we must ensure that
    the end date of all 2M is greater or equals of all finalities.
    """

    def __init__(
            self,
            updated_tree: 'ProgramTree',
            # FIXME :: The kwarg below is only useful because the validation is performed BEFORE the "Paste" action.
            # FIXME :: To remove this param, we need to call this Validator AFTER the action "paste" is Done.
            # FIXME :: (like the "update program tree version" action that uses this validator too)
            program_tree_repository: 'ProgramTreeRepository',
            trees_2m: List['ProgramTree'] = None
    ):
        super(CheckEndDateBetweenFinalitiesAndMasters2M, self).__init__()
        if trees_2m:
            assert_msg = "To use correctly this validator, make sure the ProgramTree root is of type 2M"
            for tree_2m in trees_2m:
                assert tree_2m.root_node.node_type in TrainingType.root_master_2m_types_enum(), assert_msg
        self.updated_tree = updated_tree
        self.program_tree_repository = program_tree_repository
        self.trees_2m = trees_2m

    def validate(self):
        if self.updated_tree.root_node.is_finality() or self.updated_tree.get_all_finalities():
            if self.updated_tree.root_node.is_master_2m():
                self._check_master_2m_end_year_greater_or_equal_to_its_finalities()
            else:
                self._check_finalities_end_year_greater_or_equal_to_their_masters_2m()

    def _check_master_2m_end_year_greater_or_equal_to_its_finalities(self):
        inconsistent_finalities = self._get_finalities_where_end_year_gt_root_end_year(
            self.updated_tree.root_node.end_year
        )
        if inconsistent_finalities:
            raise Program2MEndDateLowerThanItsFinalitiesException(self.updated_tree.root_node)

    def _check_finalities_end_year_greater_or_equal_to_their_masters_2m(self):
        trees_2m = self._search_master_2m_trees()
        for tree_2m in trees_2m:
            inconsistent_finalities = self._get_finalities_where_end_year_gt_root_end_year(tree_2m.root_node.end_year)
            if inconsistent_finalities:
                raise FinalitiesEndDateGreaterThanTheirMasters2MException(
                    tree_2m.root_node,
                    inconsistent_finalities
                )

    def _get_finalities_where_end_year_gt_root_end_year(self, tree_2m_end_year: int) -> Set['Node']:
        inconsistent_finalities = []
        master_2m_end_year = tree_2m_end_year or INFINITE_VALUE
        updated_node = self.updated_tree.root_node
        if updated_node.is_finality():
            end_year_of_finality = (self.updated_tree.root_node.end_year or INFINITE_VALUE)
            if end_year_of_finality > master_2m_end_year:
                inconsistent_finalities.append(updated_node)
        for finality in self.updated_tree.get_all_finalities():
            if (finality.end_year or INFINITE_VALUE) > master_2m_end_year:
                inconsistent_finalities.append(finality)

        return set(inconsistent_finalities)

    def _search_master_2m_trees(self) -> List['ProgramTree']:
        if self.trees_2m:
            return self.trees_2m
        root_identity = self.updated_tree.root_node.entity_id
        trees_2m = [
            tree for tree in self.program_tree_repository.search_from_children([root_identity])
            if tree.is_master_2m()
        ]
        return trees_2m
