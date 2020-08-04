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

from django.db import transaction

from education_group.ddd import command as command_education_group
from program_management.ddd import command as command_program_mangement

from education_group.ddd.domain.group import GroupIdentity

from education_group.ddd.service.write import create_group_service
from program_management.ddd.domain.program_tree import Path
from program_management.ddd.service.read import node_identity_service
from program_management.ddd.service.write import paste_element_service


# TODO : Implement Validator (Actually in GroupFrom via ValidationRules)
@transaction.atomic()
def create_group_and_attach(cmd: command_program_mangement.CreateGroupAndAttachCommand) -> 'GroupIdentity':
    cmd_orphan_group = __get_orphan_group_cmd_from_create_group_and_attach_cmd(cmd)
    group_id = create_group_service.create_orphan_group(cmd_orphan_group)

    cmd_paste = __get_paste_cmd(group_id, cmd.path_to_paste)
    paste_element_service.paste_element(cmd_paste)
    return group_id


def __get_orphan_group_cmd_from_create_group_and_attach_cmd(cmd: command_program_mangement.CreateGroupAndAttachCommand)\
        -> command_education_group.CreateOrphanGroupCommand:
    cmd_get_node_id = __get_node_identity_cmd(cmd.path_to_paste)
    node_id = node_identity_service.get_node_identity_from_element_id(cmd_get_node_id)

    return command_education_group.CreateOrphanGroupCommand(
        code=cmd.code,
        year=node_id.year,
        type=cmd.type,
        abbreviated_title=cmd.abbreviated_title,
        title_fr=cmd.title_fr,
        title_en=cmd.title_en,
        credits=cmd.credits,
        constraint_type=cmd.constraint_type,
        min_constraint=cmd.min_constraint,
        max_constraint=cmd.max_constraint,
        management_entity_acronym=cmd.management_entity_acronym,
        teaching_campus_name=cmd.teaching_campus_name,
        organization_name=cmd.organization_name,
        remark_fr=cmd.remark_fr,
        remark_en=cmd.remark_en,
        start_year=node_id.year,
        end_year=None
    )


def __get_node_identity_cmd(path_to_paste: Path) -> command_program_mangement.GetNodeIdentityFromElementId:
    parent_id = path_to_paste.split('|')[-1]
    return command_program_mangement.GetNodeIdentityFromElementId(element_id=int(parent_id))


def __get_paste_cmd(group_id: GroupIdentity, path_to_paste: Path) -> command_program_mangement.PasteElementCommand:
    return command_program_mangement.PasteElementCommand(
        node_to_paste_code=group_id.code,
        node_to_paste_year=group_id.year,
        path_where_to_paste=path_to_paste
    )
