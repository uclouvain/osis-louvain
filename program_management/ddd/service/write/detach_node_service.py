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

from program_management import publisher
from program_management.ddd import command
from program_management.ddd.domain import link
from program_management.ddd.domain.program_tree import PATH_SEPARATOR
from program_management.ddd.domain.service import identity_search
from program_management.ddd.repositories import persist_tree, program_tree
from program_management.ddd.repositories.tree_prerequisites import TreePrerequisitesRepository


@transaction.atomic()
def detach_node(detach_command: command.DetachNodeCommand) -> link.LinkIdentity:
    path_to_detach = detach_command.path
    commit = detach_command.commit
    root_id = int(path_to_detach.split(PATH_SEPARATOR)[0])
    program_tree_repository = program_tree.ProgramTreeRepository()

    program_tree_identity = identity_search.ProgramTreeIdentitySearch.get_from_element_id(root_id)
    working_tree = program_tree_repository.get(program_tree_identity)

    deleted_link = working_tree.detach_node(path_to_detach, program_tree_repository, TreePrerequisitesRepository())

    if commit:
        persist_tree.persist(working_tree)
        publisher.element_detached.send(None, path_detached=path_to_detach)

    return deleted_link.entity_id
