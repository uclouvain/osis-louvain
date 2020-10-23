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
from typing import Set

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType, EducationGroupTypesEnum
from osis_common.ddd.interface import BusinessExceptions
from program_management.ddd import command
from program_management.ddd.domain.node import Node
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.validators._authorized_relationship import PasteAuthorizedRelationshipValidator


def get_allowed_child_types(cmd: command.GetAllowedChildTypeCommand) -> Set[EducationGroupTypesEnum]:
    if cmd.category == Categories.TRAINING.name:
        allowed_child_types = TrainingType
    elif cmd.category == Categories.MINI_TRAINING.name:
        allowed_child_types = MiniTrainingType.get_eligible_to_be_created()
    else:
        allowed_child_types = {
            group_type for group_type in GroupType
            if group_type not in [GroupType.MAJOR_LIST_CHOICE, GroupType.MOBILITY_PARTNERSHIP_LIST_CHOICE]
        }

    if cmd.path_to_paste:
        node_to_paste_into_id = NodeIdentitySearch.get_from_element_id(
            element_id=int(cmd.path_to_paste.split('|')[-1])
        )
        tree = ProgramTreeRepository.get(node_to_paste_into_id)

        def check_paste_validator(child_type: EducationGroupTypesEnum) -> bool:
            try:
                PasteAuthorizedRelationshipValidator(
                    tree,
                    Node(node_type=child_type),
                    tree.root_node
                ).validate()
            except BusinessExceptions:
                return False
            return True
        allowed_child_types = filter(check_paste_validator, allowed_child_types)

    return {child_type for child_type in allowed_child_types}
