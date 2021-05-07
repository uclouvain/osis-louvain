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
from typing import Optional, List

import attr

from base.ddd.utils.converters import to_upper_case_converter
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import EducationGroupTypesEnum, MiniTrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._titles import Titles
from education_group.ddd.validators import validators_by_business_action
from osis_common.ddd import interface
from program_management.ddd.domain.academic_year import AcademicYear


class MiniTrainingBuilder:
    @classmethod
    def copy_to_next_year(
            self,
            mini_training_from: 'MiniTraining',
            mini_training_repository: 'MiniTrainingRepository') -> 'MiniTraining':
        validators_by_business_action.CopyMiniTrainingValidatorList(mini_training_from).validate()
        identity_next_year = attr.evolve(mini_training_from.entity_identity, year=mini_training_from.year + 1)
        try:
            mini_training_next_year = mini_training_repository.get(identity_next_year)
            mini_training_next_year.update_from_other_training(mini_training_from)
        except exception.MiniTrainingNotFoundException:
            mini_training_next_year = attr.evolve(
                mini_training_from,
                entity_identity=identity_next_year,
                entity_id=identity_next_year,
            )
        return mini_training_next_year

    @classmethod
    def build_from_create_cmd(self, cmd: command.CreateMiniTrainingCommand):
        mini_training_id = MiniTrainingIdentity(acronym=cmd.abbreviated_title, year=cmd.year)
        titles = Titles(title_fr=cmd.title_fr, title_en=cmd.title_en)
        management_entity = Entity(acronym=cmd.management_entity_acronym)

        mini_training_domain_obj = MiniTraining(
            entity_identity=mini_training_id,
            entity_id=mini_training_id,
            code=cmd.code,
            type=MiniTrainingType[cmd.type],
            keywords=cmd.keywords,
            abbreviated_title=cmd.abbreviated_title,
            titles=titles,
            status=ActiveStatusEnum[cmd.status],
            schedule_type=ScheduleTypeEnum[cmd.schedule_type],
            credits=cmd.credits,
            management_entity=management_entity,
            start_year=cmd.start_year,
            end_year=cmd.end_year,

        )

        validators_by_business_action.CreateMiniTrainingValidatorList(mini_training_domain_obj).validate()

        return mini_training_domain_obj


builder = MiniTrainingBuilder()


@attr.s(frozen=True, slots=True)
class MiniTrainingIdentity(interface.EntityIdentity):
    # TODO: Rename acronym to abbreviated_title
    acronym = attr.ib(type=str, converter=to_upper_case_converter)
    year = attr.ib(type=int)


@attr.s(slots=True, eq=False, hash=False)
class MiniTraining(interface.RootEntity):
    entity_id = entity_identity = attr.ib(type=MiniTrainingIdentity)
    code = attr.ib(type=str, converter=to_upper_case_converter)
    type = attr.ib(type=EducationGroupTypesEnum)
    # TODO: Make a computed property instead of acronym (see TODO in MiniTrainingIdentity)
    abbreviated_title = attr.ib(type=str, converter=to_upper_case_converter)
    titles = attr.ib(type=Titles)
    status = attr.ib(type=ActiveStatusEnum)
    schedule_type = attr.ib(type=ScheduleTypeEnum)
    credits = attr.ib(type=int)
    management_entity = attr.ib(type=Entity)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int], default=None)
    keywords = attr.ib(type=str, default="")

    @property
    def acronym(self) -> str:
        return self.entity_id.acronym

    @property
    def year(self) -> int:
        return self.entity_id.year

    @property
    def academic_year(self) -> AcademicYear:
        return AcademicYear(self.year)

    def has_same_values_as(self, other: 'MiniTraining') -> bool:
        return not bool(self.get_conflicted_fields(other))

    def get_conflicted_fields(self, other: 'MiniTraining') -> List[str]:
        fields_not_to_compare = ("year", "entity_id", "entity_identity", 'acronym')
        conflicted_fields = []
        for field_name in other.__slots__:
            if field_name in fields_not_to_compare:
                continue
            if getattr(self, field_name) != getattr(other, field_name):
                conflicted_fields.append(field_name)
        return conflicted_fields

    def update(self, data: 'UpdateMiniTrainingData'):
        data_as_dict = attr.asdict(data, recurse=False)
        for field, new_value in data_as_dict.items():
            setattr(self, field, new_value)
        validators_by_business_action.UpdateMiniTrainingValidatorList(self)
        return self

    def update_from_other_training(self, other: 'MiniTraining'):
        fields_not_to_update = (
            "year", "acronym", "entity_id", "entity_identity", "identity_through_years"
        )
        for field in other.__slots__:
            if field in fields_not_to_update:
                continue
            value = getattr(other, field)
            setattr(self, field, value)


@attr.s(frozen=True, slots=True, kw_only=True)
class UpdateMiniTrainingData:
    credits = attr.ib(type=int)
    titles = attr.ib(type=Titles)
    status = attr.ib(type=ActiveStatusEnum, default=ActiveStatusEnum.ACTIVE)
    keywords = attr.ib(type=str, default="")
    schedule_type = attr.ib(type=ScheduleTypeEnum, default=ScheduleTypeEnum.DAILY)
    management_entity = attr.ib(type=Entity, default=None)
    end_year = attr.ib(type=int, default=None)
    teaching_campus = attr.ib(type=Campus, default=None)
