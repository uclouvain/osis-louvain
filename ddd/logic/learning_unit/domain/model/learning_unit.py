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
from typing import List

import attr

from base.models.enums.internship_subtypes import InternshipSubtype
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from ddd.logic.learning_unit.domain.model._partim import Partim, PartimBuilder
from ddd.logic.learning_unit.domain.model._titles import Titles
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from ddd.logic.shared_kernel.language.domain.model.language import LanguageIdentity
from osis_common.ddd import interface
from ddd.logic.learning_unit.commands import CreatePartimCommand
from ddd.logic.learning_unit.domain.model._remarks import Remarks


@attr.s(frozen=True, slots=True)
class LearningUnitIdentity(interface.EntityIdentity):
    academic_year = attr.ib(type=AcademicYearIdentity)
    code = attr.ib(type=str)

    def __str__(self):
        return "{} - ({})".format(self.code, self.academic_year)

    @property
    def year(self) -> int:
        return self.academic_year.year

    def get_next_year(self):
        return self.year + 1


@attr.s(slots=True, hash=False, eq=False)
class LearningUnit(interface.RootEntity):
    entity_id = attr.ib(type=LearningUnitIdentity)
    titles = attr.ib(type=Titles)
    credits = attr.ib(type=int)
    internship_subtype = attr.ib(type=InternshipSubtype)
    responsible_entity_identity = attr.ib(type=UCLEntityIdentity)
    periodicity = attr.ib(type=PeriodicityEnum)
    language_id = attr.ib(type=LanguageIdentity)
    remarks = attr.ib(type=Remarks)
    partims = attr.ib(type=List[Partim])
    # lecturing_part = attr.ib(type=LecturingPart)
    # practical_part = attr.ib(type=PracticalPart)

    @property
    def academic_year(self) -> 'AcademicYearIdentity':
        return self.entity_id.academic_year

    @property
    def code(self) -> str:
        return self.entity_id.code

    def contains_partim_subdivision(self, subdivision: str) -> bool:
        return subdivision in {p.subdivision for p in self.partims}

    def create_partim(self, create_partim_cmd: 'CreatePartimCommand') -> None:
        partim = PartimBuilder.build_from_command(
            cmd=create_partim_cmd,
            learning_unit=self,
        )
        self.partims.append(partim)


class CourseLearningUnit(LearningUnit):
    type = LearningContainerYearType.COURSE


class InternshipLearningUnit(LearningUnit):
    type = LearningContainerYearType.INTERNSHIP


class DissertationLearningUnit(LearningUnit):
    type = LearningContainerYearType.DISSERTATION


class OtherCollectiveLearningUnit(LearningUnit):
    type = LearningContainerYearType.OTHER_COLLECTIVE


class OtherIndividualLearningUnit(LearningUnit):
    type = LearningContainerYearType.OTHER_INDIVIDUAL


class MasterThesisLearningUnit(LearningUnit):
    type = LearningContainerYearType.MASTER_THESIS


class ExternalLearningUnit(LearningUnit):
    type = LearningContainerYearType.EXTERNAL
