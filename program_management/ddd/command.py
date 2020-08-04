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
from typing import Optional, Set

import attr

import attr

from base.models.enums.link_type import LinkTypes
from education_group.ddd import command as education_group_command
from osis_common.ddd import interface
from program_management.ddd.business_types import *


class DetachNodeCommand(interface.CommandRequest):
    def __init__(self, path_where_to_detach: str, commit: bool):
        self.path = path_where_to_detach
        self.commit = commit

    def __eq__(self, other):
        if isinstance(other, DetachNodeCommand):
            return self.path == other.path and self.commit == other.commit
        return False


class OrderLinkCommand(interface.CommandRequest):
    # To implement
    pass


class CreateProgramTreeVersionCommand(interface.CommandRequest):
    # To implement
    pass


class CopyElementCommand(interface.CommandRequest):
    def __init__(self, user_id: int, element_code: str, element_year: int):
        self.user_id = user_id
        self.element_code = element_code
        self.element_year = element_year

    def __eq__(self, other):
        if isinstance(other, CopyElementCommand):
            return (self.user_id, self.element_code, self.element_year) == \
                   (other.user_id, other.element_code, other.element_year)
        return False


class CutElementCommand(interface.CommandRequest):
    def __init__(self, user_id: int, element_code: str, element_year: int, path_to_detach: str):
        self.user_id = user_id
        self.element_code = element_code
        self.element_year = element_year
        self.path_to_detach = path_to_detach

    def __eq__(self, other):
        if isinstance(other, CutElementCommand):
            return (self.user_id, self.element_code, self.element_year, self.path_to_detach) == \
                   (other.user_id, other.element_code, other.element_year, other.path_to_detach)
        return False


@attr.s(frozen=True, slots=True)
class PasteElementCommand(interface.CommandRequest):
    node_to_paste_code = attr.ib(type=str)
    node_to_paste_year = attr.ib(type=int)
    path_where_to_paste = attr.ib(type='Path')
    access_condition = attr.ib(type=bool, default=False)
    is_mandatory = attr.ib(type=bool, default=True)
    block = attr.ib(type=Optional[int], default=None)
    link_type = attr.ib(type=Optional[LinkTypes], default=None)
    comment = attr.ib(type=str, factory=str)
    comment_english = attr.ib(type=str, factory=str)
    relative_credits = attr.ib(type=Optional[int], default=None)
    path_where_to_detach = attr.ib(type=Optional['Path'], default=None)


class CheckPasteNodeCommand(interface.CommandRequest):
    def __init__(
            self,
            root_id: int,
            node_to_past_code: str,
            node_to_paste_year: int,
            path_to_paste: str,
            path_to_detach: Optional[str]
    ):
        self.root_id = root_id
        self.node_to_paste_code = node_to_past_code
        self.node_to_paste_year = node_to_paste_year
        self.path_to_detach = path_to_detach
        self.path_to_paste = path_to_paste

    def __eq__(self, other):
        if isinstance(other, CheckPasteNodeCommand):
            return (self.root_id, self.node_to_paste_code, self.node_to_paste_year,
                    self.path_to_detach, self.path_to_paste) == \
                   (other.root_id, other.node_to_paste_code, other.node_to_paste_year,
                    other.path_to_detach, other.path_to_paste)
        return False

    def __repr__(self) -> str:
        parameters = ", ".join([str(self.root_id), str(self.node_to_paste_code),
                                str(self.node_to_paste_year), str(self.path_to_paste), str(self.path_to_detach)])
        return "CheckPasteNodeCommand({parameters})".format(parameters=parameters)


class OrderUpLinkCommand(interface.CommandRequest):
    def __init__(self, path: str):
        self.path = path

    def __eq__(self, other):
        if isinstance(other, OrderUpLinkCommand):
            return self.path == other.path
        return False


class OrderDownLinkCommand(interface.CommandRequest):
    def __init__(self, path: str):
        self.path = path

    def __eq__(self, other):
        if isinstance(other, OrderDownLinkCommand):
            return self.path == other.path
        return False


class GetAllowedChildTypeCommand(interface.CommandRequest):
    def __init__(
            self,
            category: str,
            path_to_paste: str = None,
    ):
        self.category = category
        self.path_to_paste = path_to_paste

    def __repr__(self) -> str:
        parameters = ", ".join([str(self.category), str(self.path_to_paste)])
        return "GetAllowedChildTypeCommand({parameters})".format(parameters=parameters)


@attr.s(frozen=True, slots=True)
class GetDefaultLinkType(interface.CommandRequest):
    path_to_paste = attr.ib(type=str)
    child_code = attr.ib(type=str)
    child_year = attr.ib(type=int)


class CreateGroupAndAttachCommand(interface.CommandRequest):
    def __init__(
            self,
            code: str,
            type: str,
            abbreviated_title: str,
            title_fr: str,
            title_en: str,
            credits: int,
            constraint_type: str,
            min_constraint: int,
            max_constraint: int,
            management_entity_acronym: str,
            teaching_campus_name: str,
            organization_name: str,
            remark_fr: str,
            remark_en: str,
            path_to_paste: str,
    ):
        self.code = code
        self.type = type
        self.abbreviated_title = abbreviated_title
        self.title_fr = title_fr
        self.title_en = title_en
        self.credits = credits
        self.constraint_type = constraint_type
        self.min_constraint = min_constraint
        self.max_constraint = max_constraint
        self.management_entity_acronym = management_entity_acronym
        self.teaching_campus_name = teaching_campus_name
        self.organization_name = organization_name
        self.remark_fr = remark_fr
        self.remark_en = remark_en
        self.path_to_paste = path_to_paste

    def __repr__(self) -> str:
        parameters = ", ".join([
            str(self.code), str(self.type), str(self.abbreviated_title), str(self.title_fr),
            str(self.title_en), str(self.credits), str(self.constraint_type), str(self.min_constraint),
            str(self.max_constraint), str(self.management_entity_acronym), str(self.teaching_campus_name),
            str(self.organization_name), str(self.remark_fr), str(self.remark_en), str(self.path_to_paste), ])
        return "CreateGroupAndAttachCommand({parameters})".format(parameters=parameters)


@attr.s(frozen=True, slots=True)
class CreateMiniTrainingAndPasteCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    abbreviated_title = attr.ib(type=str)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    keywords = attr.ib(type=str)
    status = attr.ib(type=str)
    schedule_type = attr.ib(type=str)
    credits = attr.ib(type=int)
    constraint_type = attr.ib(type=str)
    min_constraint = attr.ib(type=int)
    max_constraint = attr.ib(type=int)
    management_entity_acronym = attr.ib(type=str)
    teaching_campus_name = attr.ib(type=str)
    organization_name = attr.ib(type=str)
    remark_fr = attr.ib(type=str)
    remark_en = attr.ib(type=str)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int])
    path_to_paste = attr.ib(type=str)


class GetNodeIdentityFromElementId(interface.CommandRequest):
    def __init__(self, element_id: int):
        self.element_id = element_id

    def __repr__(self) -> str:
        parameters = ", ".join([str(self.element_id)])
        return "GetNodeIdentityFromElementId({parameters})".format(parameters=parameters)


class SearchAllVersionsFromRootNodesCommand(interface.CommandRequest):
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year


class GetProgramTree(interface.CommandRequest):
    def __init__(self, code: str, year: int):
        self.code = code
        self.year = year

    def __repr__(self) -> str:
        parameters = ", ".join([str(self.code), str(self.year)])
        return "GetProgramTree({parameters})".format(parameters=parameters)


@attr.s(frozen=True, slots=True)
class UpdateLinkCommand(interface.CommandRequest):
    child_node_code = attr.ib(type=str)
    child_node_year = attr.ib(type=int)

    access_condition = attr.ib(type=bool)
    is_mandatory = attr.ib(type=bool)
    block = attr.ib(type=str)
    link_type = attr.ib(type=str)
    comment = attr.ib(type=str)
    comment_english = attr.ib(type=str)
    relative_credits = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class BulkUpdateLinkCommand(interface.CommandRequest):
    parent_node_code = attr.ib(type=str)
    parent_node_year = attr.ib(type=int)

    update_link_cmds = attr.ib(factory=list, type=UpdateLinkCommand)


@attr.s(frozen=True, slots=True)
class CreateStandardVersionCommand(interface.CommandRequest):
    offer_acronym = attr.ib(type=str)
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class PostponeProgramTreeCommand(interface.CommandRequest):
    from_code = attr.ib(type=str)
    from_year = attr.ib(type=int)
    offer_acronym = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class CopyProgramTreeToNextYearCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class PostponeProgramTreeVersionCommand(interface.CommandRequest):
    from_offer_acronym = attr.ib(type=str)
    from_version_name = attr.ib(type=str)
    from_year = attr.ib(type=int)
    from_is_transition = attr.ib(type=bool)
    from_code = attr.ib(type=str, default=None)


@attr.s(frozen=True, slots=True)
class CopyTreeVersionToNextYearCommand(interface.CommandRequest):
    from_year = attr.ib(type=int)
    from_offer_acronym = attr.ib(type=str)
    from_offer_code = attr.ib(type=str)
    from_version_name = attr.ib(type=str)
    from_is_transition = attr.ib(type=bool)


@attr.s(frozen=True, slots=True)
class CreateAndAttachTrainingCommand(education_group_command.CreateTrainingCommand):
    path_to_paste = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DeleteProgramTreeCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class DeleteAllProgramTreeCommand(interface.CommandRequest):
    code = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DeleteStandardVersionCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class DeleteNodeCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    node_type = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class GetProgramTreesFromNodeCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class GetProgramTreesVersionFromNodeCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
