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
from typing import Optional

from django.contrib.auth import models

from base.models.enums.link_type import LinkTypes
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.models.enums import node_type


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


class PasteElementCommand(interface.CommandRequest):
    def __init__(
            self,
            node_to_paste_code: str,
            node_to_paste_year: int,
            path_where_to_paste: 'Path',
            access_condition: Optional[bool],
            is_mandatory: Optional[bool],
            block: Optional[int],
            link_type: Optional[LinkTypes],
            comment: str,
            comment_english: str,
            relative_credits: Optional[int],
            path_where_to_detach: Optional['Path']
    ) -> None:
        self.node_to_paste_code = node_to_paste_code
        self.node_to_paste_year = node_to_paste_year
        self.path_where_to_paste = path_where_to_paste
        self.access_condition = access_condition
        self.is_mandatory = is_mandatory
        self.block = block
        self.link_type = link_type
        self.comment = comment
        self.comment_english = comment_english
        self.relative_credits = relative_credits
        self.path_where_to_detach = path_where_to_detach


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
