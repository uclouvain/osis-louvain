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
from typing import Optional

import attr

from education_group.ddd.business_types import *
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import EducationGroupTypesEnum, MiniTrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.validators import validators_by_business_action
from osis_common.ddd import interface


class MiniTrainingBuilder:
    @classmethod
    def copy_to_next_year(
            self,
            mini_training_from: 'MiniTraining',
            mini_training_repository: 'MiniTrainingRepository') -> 'MiniTraining':

        identity_next_year = attr.evolve(mini_training_from.entity_identity, year=mini_training_from.year + 1)
        try:
            mini_training_next_year = mini_training_repository.get(identity_next_year)
        except exception.MiniTrainingNotFoundException:
            # Case create training next year
            mini_training_next_year = attr.evolve(  # Copy to new object
                mini_training_from,
                entity_identity=identity_next_year,
                entity_id=identity_next_year,
            )
            validators_by_business_action.CopyMiniTrainingValidatorList(mini_training_next_year)
        return mini_training_next_year

    @classmethod
    def build_from_create_cmd(self, cmd: command.CreateMiniTrainingCommand):
        mini_training_id = MiniTrainingIdentity(acronym=cmd.abbreviated_title, year=cmd.year)
        titles = Titles(title_fr=cmd.title_fr, title_en=cmd.title_en)
        management_entity = Entity(acronym=cmd.management_entity_acronym)
        teaching_campus = Campus(
            name=cmd.teaching_campus_name,
            university_name=cmd.organization_name,
        )

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
            teaching_campus=teaching_campus,
            start_year=cmd.start_year,
            end_year=cmd.end_year,

        )

        validators_by_business_action.CreateMiniTrainingValidatorList(mini_training_domain_obj).validate()

        return mini_training_domain_obj


builder = MiniTrainingBuilder()


@attr.s(frozen=True, slots=True)
class MiniTrainingIdentity(interface.EntityIdentity):
    acronym = attr.ib(type=str, converter=lambda code: code.upper())
    year = attr.ib(type=int)


@attr.s(slots=True, eq=False, hash=False)
class MiniTraining(interface.RootEntity):
    entity_id = entity_identity = attr.ib(type=MiniTrainingIdentity)
    code = attr.ib(type=str)
    type = attr.ib(type=EducationGroupTypesEnum)
    abbreviated_title = attr.ib(type=str)
    titles = attr.ib(type=Titles)
    status = attr.ib(type=ActiveStatusEnum)
    schedule_type = attr.ib(type=ScheduleTypeEnum)
    credits = attr.ib(type=int)
    management_entity = attr.ib(type=Entity)
    teaching_campus = attr.ib(type=Campus)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int], default=None)
    keywords = attr.ib(type=str, default="")

    @property
    def acronym(self) -> str:
        return self.entity_id.acronym

    @property
    def year(self) -> int:
        return self.entity_id.year
