##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_common.ddd import interface
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from ddd.logic.learning_unit.domain.validator.exceptions import LearningUnitUsedInProgramTreeException
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnitIdentity


class LearningUnitCanBeDeleted(interface.DomainService):

    def validate(
            self,
            learning_unit_identity: 'LearningUnitIdentity',
            program_tree_repo: 'ProgramTreeRepository'
    ):
        self.__check_if_is_used_in_program_tree(learning_unit_identity, program_tree_repo)

    def __check_if_is_used_in_program_tree(
            self,
            learning_unit_identity: 'LearningUnitIdentity',
            program_tree_repo: 'ProgramTreeRepository'
    ):
        node_identity = NodeIdentity(code=learning_unit_identity.code, year=learning_unit_identity.academic_year.year)
        programs_using_learning_unit = program_tree_repo.search_from_children([node_identity])
        if programs_using_learning_unit:
            identities = [prog.entity_id for prog in programs_using_learning_unit]
            raise LearningUnitUsedInProgramTreeException(learning_unit_identity, identities)
