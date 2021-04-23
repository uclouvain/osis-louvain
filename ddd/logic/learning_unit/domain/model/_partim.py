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
import attr

from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from ddd.logic.shared_kernel.language.builder.language_identity_builder import LanguageIdentityBuilder
from ddd.logic.shared_kernel.language.domain.model.language import LanguageIdentity
from osis_common.ddd import interface
from ddd.logic.learning_unit.commands import CreatePartimCommand
from ddd.logic.learning_unit.domain.model._remarks import Remarks
from ddd.logic.learning_unit.domain.validator.validators_by_business_action import CreatePartimValidatorList
from ddd.logic.learning_unit.business_types import *


@attr.s(frozen=True, slots=True)
class PartimIdentity(interface.EntityIdentity):
    subdivision = attr.ib(type=str)

    def __str__(self):
        return self.subdivision


class PartimBuilder:
    @classmethod
    def build_from_command(cls, cmd: 'CreatePartimCommand', learning_unit: 'LearningUnit') -> 'Partim':
        CreatePartimValidatorList(
            learning_unit=learning_unit,
            subdivision=cmd.subdivision,
        ).validate()
        return Partim(
            entity_id=PartimIdentity(subdivision=cmd.subdivision),
            title_fr=cmd.title_fr,
            title_en=cmd.title_en,
            credits=cmd.credits,
            periodicity=PeriodicityEnum[cmd.periodicity],
            language_id=LanguageIdentityBuilder.build_from_code_iso(cmd.iso_code),
            remarks=Remarks(
                faculty=cmd.remark_faculty,
                publication_fr=cmd.remark_publication_fr,
                publication_en=cmd.remark_publication_en,
            ),
        )


@attr.s(slots=True, hash=False, eq=False)
class Partim(interface.Entity):
    entity_id = attr.ib(type=PartimIdentity)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    periodicity = attr.ib(type=PeriodicityEnum)
    language_id = attr.ib(type=LanguageIdentity)
    remarks = attr.ib(type=Remarks)

    @property
    def subdivision(self) -> str:
        return self.entity_id.subdivision
