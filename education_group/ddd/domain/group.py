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
import copy
from typing import Optional, List

import attr

from base.ddd.utils.converters import to_upper_case_converter
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import EducationGroupTypesEnum, GroupType, TrainingType, MiniTrainingType
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.command import UpdateGroupCommand
from education_group.ddd.domain import exception
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain.service.enum_converter import EducationGroupTypeConverter
from education_group.ddd.validators.validators_by_business_action import UpdateGroupValidatorList, \
    CopyGroupValidatorList, CreateGroupValidatorList
from osis_common.ddd import interface
from program_management.ddd.domain.academic_year import AcademicYear


class GroupBuilder:
    @classmethod
    def copy_to_next_year(cls, group_from: 'Group', group_repository: 'GroupRepository') -> 'Group':
        identity_next_year = GroupIdentity(code=group_from.code, year=group_from.year + 1)
        CopyGroupValidatorList(group_from).validate()
        try:
            group_next_year = group_repository.get(identity_next_year)
            group_next_year.update_from_other_group(group_from)
        except exception.GroupNotFoundException:
            group_next_year = copy.deepcopy(group_from)
            group_next_year.entity_id = identity_next_year
        cls._update_end_year(group_next_year)
        return group_next_year

    @staticmethod
    def _update_end_year(group: 'Group') -> None:
        if not group.end_year:
            return
        if group.year > group.end_year:
            group.end_year = group.year

    @classmethod
    def build_from_create_cmd(cls, cmd: command.CreateOrphanGroupCommand):
        group_id = GroupIdentity(code=cmd.code, year=cmd.year)
        titles = Titles(title_fr=cmd.title_fr, title_en=cmd.title_en)
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum[cmd.constraint_type] if cmd.constraint_type else None,
            minimum=cmd.min_constraint,
            maximum=cmd.max_constraint
        )
        management_entity = Entity(acronym=cmd.management_entity_acronym)
        teaching_campus = Campus(
            name=cmd.teaching_campus_name,
            university_name=cmd.organization_name,
        )
        remark = Remark(text_fr=cmd.remark_fr, text_en=cmd.remark_en)

        created_group = Group(
            entity_identity=group_id,
            entity_id=group_id,
            type=EducationGroupTypeConverter.convert_type_str_to_enum(cmd.type),
            abbreviated_title=cmd.abbreviated_title,
            titles=titles,
            credits=cmd.credits,
            content_constraint=content_constraint,
            management_entity=management_entity,
            teaching_campus=teaching_campus,
            remark=remark,
            start_year=cmd.start_year,
            end_year=cmd.end_year
        )
        CreateGroupValidatorList(created_group).validate()
        return created_group


builder = GroupBuilder()


@attr.s(frozen=True, slots=True)
class GroupIdentity(interface.EntityIdentity):
    code = attr.ib(type=str, converter=to_upper_case_converter)
    year = attr.ib(type=int)


@attr.s(slots=True)
class Group(interface.RootEntity):
    entity_id = entity_identity = attr.ib(type=GroupIdentity)
    type = attr.ib(type=EducationGroupTypesEnum)
    abbreviated_title = attr.ib(type=str, converter=to_upper_case_converter)
    titles = attr.ib(type=Titles)
    credits = attr.ib(type=int)
    content_constraint = attr.ib(type=ContentConstraint)
    management_entity = attr.ib(type=Entity)
    teaching_campus = attr.ib(type=Campus)
    remark = attr.ib(type=Remark)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int], default=None)

    @property
    def academic_year(self) -> AcademicYear:
        return AcademicYear(self.year)

    @property
    def code(self) -> str:
        return self.entity_id.code

    @property
    def year(self) -> int:
        return self.entity_id.year

    @property
    def academic_year(self) -> AcademicYear:
        return AcademicYear(self.year)

    def is_minor_major_option_list_choice(self):
        return self.type.name in GroupType.minor_major_option_list_choice()

    def is_training(self):
        return self.type in TrainingType

    def is_mini_training(self):
        return self.type in MiniTrainingType

    def update(self, cmd: 'UpdateGroupCommand'):
        self.abbreviated_title = cmd.abbreviated_title.upper()
        self.titles = Titles(title_fr=cmd.title_fr, title_en=cmd.title_en)
        self.credits = cmd.credits
        self.content_constraint = ContentConstraint(
            type=ConstraintTypeEnum[cmd.constraint_type] if cmd.constraint_type else None,
            minimum=cmd.min_constraint,
            maximum=cmd.max_constraint
        )
        self.management_entity = Entity(acronym=cmd.management_entity_acronym)
        self.teaching_campus = Campus(
            name=cmd.teaching_campus_name,
            university_name=cmd.organization_name
        )
        self.remark = Remark(text_fr=cmd.remark_fr, text_en=cmd.remark_en)
        self.end_year = cmd.end_year
        UpdateGroupValidatorList(self).validate()
        return self

    def has_same_values_as(self, other_group: 'Group') -> bool:
        return not bool(self.get_conflicted_fields(other_group))

    def get_conflicted_fields(self, other_group: 'Group') -> List[str]:
        fields_not_to_consider = ("year", "entity_id", "entity_identity")
        conflicted_fields = []
        for field_name in self.__slots__:
            if field_name in fields_not_to_consider:
                continue
            if getattr(self, field_name) != getattr(other_group, field_name):
                conflicted_fields.append(field_name)
        return conflicted_fields

    def update_from_other_group(self, other_group: 'Group'):
        fields_not_to_update = (
            "year", "code", "entity_id", "entity_identity"
        )
        for field in other_group.__slots__:
            if field in fields_not_to_update:
                continue
            value = getattr(other_group, field)
            setattr(self, field, value)
