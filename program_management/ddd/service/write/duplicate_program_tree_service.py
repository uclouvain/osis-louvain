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

from django.db import transaction

from education_group.ddd.service.write import create_group_service
from program_management.ddd import command
from program_management.ddd.domain import program_tree as tree_domain
from program_management.ddd.domain.service import validation_rule as validation_rule_service
from program_management.ddd.repositories import program_tree as tree_repository


@transaction.atomic()
def create_and_fill_from_existing_tree(cmd: command.DuplicateProgramTree) -> 'ProgramTreeIdentity':

    # GIVEN
    program_tree_identity = tree_domain.ProgramTreeIdentity(code=cmd.from_root_code, year=cmd.from_root_year)
    existing_tree = tree_repository.ProgramTreeRepository().get(entity_id=program_tree_identity)

    # WHEN
    program_tree = tree_domain.ProgramTreeBuilder().create_and_fill_from_program_tree(
        duplicate_from=existing_tree,
        duplicate_to_transition=cmd.duplicate_to_transition,
        override_end_year_to=cmd.override_end_year_to,
        override_start_year_to=cmd.override_start_year_to
    )

    # TODO: Move validation_rule to initial credit Node
    validation_rule = validation_rule_service.FieldValidationRule.get(
        program_tree.root_node.node_type, 'credits', is_version=True
    )
    program_tree.root_node.credits = validation_rule.initial_value

    # THEN
    program_tree_identity = tree_repository.ProgramTreeRepository().create(
        program_tree=program_tree,
        create_orphan_group_service=create_group_service.create_orphan_group
    )

    return program_tree_identity
