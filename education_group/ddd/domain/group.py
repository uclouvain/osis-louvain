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

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import EducationGroupTypesEnum, GroupType
from education_group.ddd import command
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain.service.enum_converter import EducationGroupTypeConverter
from education_group.ddd.validators.validators_by_business_action import UpdateGroupValidatorList
from osis_common.ddd import interface


class GroupBuilder:
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

        return Group(
            entity_identity=group_id,
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

    @classmethod
    def build_next_year_group(cls, from_group: 'Group'):
        group = copy.deepcopy(from_group)
        group.entity_id = GroupIdentity(code=from_group.code, year=from_group.year + 1)
        return group


builder = GroupBuilder()


class GroupIdentity(interface.EntityIdentity):
    def __init__(self, code: str, year: int):
        self.code = code.upper()
        self.year = year

    def __hash__(self):
        return hash(self.code + str(self.year))

    def __eq__(self, other):
        return self.code == other.code and self.year == other.year


class Group(interface.RootEntity):
    def __init__(
        self,
        entity_identity: 'GroupIdentity',
        type: EducationGroupTypesEnum,
        abbreviated_title: str,
        titles: Titles,
        credits: int,
        content_constraint: ContentConstraint,
        management_entity: Entity,
        teaching_campus: Campus,
        remark: Remark,
        start_year: int,
        end_year: int = None,
    ):
        super(Group, self).__init__(entity_id=entity_identity)
        self.entity_id = entity_identity
        self.type = type
        self.abbreviated_title = abbreviated_title.upper()
        self.titles = titles
        self.credits = credits
        self.content_constraint = content_constraint
        self.management_entity = management_entity
        self.teaching_campus = teaching_campus
        self.remark = remark
        self.start_year = start_year
        self.end_year = end_year

    @property
    def code(self) -> str:
        return self.entity_id.code

    @property
    def year(self) -> int:
        return self.entity_id.year

    def is_minor_major_option_list_choice(self):
        return self.type.name in GroupType.minor_major_option_list_choice()

    def update(
            self,
            abbreviated_title: str,
            titles: Titles,
            credits: int,
            content_constraint: ContentConstraint,
            management_entity: Entity,
            teaching_campus: Campus,
            remark: Remark
    ):
        self.abbreviated_title = abbreviated_title.upper()
        self.titles = titles
        self.credits = credits
        self.content_constraint = content_constraint
        self.management_entity = management_entity
        self.teaching_campus = teaching_campus
        self.remark = remark
        UpdateGroupValidatorList(self).validate()
        return self
