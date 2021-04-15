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
from typing import List, Type

import attr

from base.models.enums.internship_subtypes import InternshipSubtype
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from ddd.logic.learning_unit.builder.learning_unit_identity_builder import LearningUnitIdentityBuilder
from ddd.logic.learning_unit.builder.ucl_entity_identity_builder import UclEntityIdentityBuilder
from ddd.logic.learning_unit.commands import CreateLearningUnitCommand
from ddd.logic.learning_unit.domain.model._remarks import Remarks
from ddd.logic.learning_unit.domain.model._titles import Titles
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnit, LearningUnitIdentity, CourseLearningUnit, \
    InternshipLearningUnit, DissertationLearningUnit, OtherCollectiveLearningUnit, OtherIndividualLearningUnit, \
    MasterThesisLearningUnit, ExternalLearningUnit
from ddd.logic.learning_unit.domain.model.responsible_entity import UCLEntityIdentity
from ddd.logic.learning_unit.domain.validator.validators_by_business_action import \
    CopyLearningUnitToNextYearValidatorList, \
    CreateLearningUnitValidatorList
from ddd.logic.learning_unit.dtos import LearningUnitFromRepositoryDTO
from ddd.logic.shared_kernel.language.builder.language_identity_builder import LanguageIdentityBuilder
from osis_common.ddd.interface import RootEntityBuilder


class LearningUnitBuilder(RootEntityBuilder):

    @classmethod
    def build_from_command(
            cls,
            cmd: 'CreateLearningUnitCommand',
            all_existing_identities: List['LearningUnitIdentity'],
            responsible_entity_identity: UCLEntityIdentity
    ) -> 'LearningUnit':
        CreateLearningUnitValidatorList(
            command=cmd,
            all_existing_identities=all_existing_identities
        ).validate()
        dto = cmd
        return _get_learning_unit_class(dto.type)(
            entity_id=LearningUnitIdentityBuilder.build_from_code_and_year(dto.code, dto.academic_year),
            titles=_build_titles(
                dto.common_title_fr,
                dto.specific_title_fr,
                dto.common_title_en,
                dto.specific_title_en
            ),
            credits=dto.credits,
            internship_subtype=InternshipSubtype[dto.internship_subtype],
            responsible_entity_identity=responsible_entity_identity,
            periodicity=PeriodicityEnum[dto.periodicity],
            language_id=_build_language(dto.iso_code),
            remarks=_build_remarks(dto.remark_faculty, dto.remark_publication_fr, dto.remark_publication_en),
        )

    @classmethod
    def build_from_repository_dto(
            cls,
            dto: 'LearningUnitFromRepositoryDTO',
    ) -> 'LearningUnit':
        return _get_learning_unit_class(dto.type)(
            entity_id=LearningUnitIdentityBuilder.build_from_code_and_year(dto.code, dto.year),
            type=LearningContainerYearType[dto.type],
            titles=_build_titles(
                dto.common_title_fr,
                dto.specific_title_fr,
                dto.common_title_en,
                dto.specific_title_en
            ),
            credits=dto.credits,
            internship_subtype=InternshipSubtype[dto.internship_subtype],
            responsible_entity_identity=UclEntityIdentityBuilder.build_from_code(dto.responsible_entity_code),
            periodicity=PeriodicityEnum[dto.periodicity],
            language_id=_build_language(dto.iso_code),
            remarks=_build_remarks(dto.remark_faculty, dto.remark_publication_fr, dto.remark_publication_en),
        )

    @classmethod
    def copy_to_next_year(
            cls,
            learning_unit: 'LearningUnit',
            all_existing_lear_unit_identities: List['LearningUnitIdentity']
    ) -> 'LearningUnit':
        CopyLearningUnitToNextYearValidatorList(learning_unit.entity_id, all_existing_lear_unit_identities).validate()
        learning_unit_next_year = attr.evolve(
            learning_unit,
            entity_id=LearningUnitIdentityBuilder.build_for_next_year(learning_unit.entity_id)
        )
        return learning_unit_next_year


def _get_learning_unit_class(type: str) -> Type[LearningUnit]:
    subclass = None
    if type == LearningContainerYearType.COURSE.name:
        subclass = CourseLearningUnit
    elif type == LearningContainerYearType.INTERNSHIP.name:
        subclass = InternshipLearningUnit
    elif type == LearningContainerYearType.DISSERTATION.name:
        subclass = DissertationLearningUnit
    elif type == LearningContainerYearType.OTHER_COLLECTIVE.name:
        subclass = OtherCollectiveLearningUnit
    elif type == LearningContainerYearType.OTHER_INDIVIDUAL.name:
        subclass = OtherIndividualLearningUnit
    elif type == LearningContainerYearType.MASTER_THESIS.name:
        subclass = MasterThesisLearningUnit
    elif type == LearningContainerYearType.EXTERNAL.name:
        subclass = ExternalLearningUnit
    return subclass


def _build_remarks(remark_faculty: str, remark_publication_fr: str, remark_publication_en: str):
    return Remarks(
        faculty=remark_faculty,
        publication_fr=remark_publication_fr,
        publication_en=remark_publication_en,
    )


def _build_language(iso_code: str):
    return LanguageIdentityBuilder.build_from_code_iso(iso_code)


def _build_titles(common_title_fr: str, specific_title_fr: str, common_title_en: str, specific_title_en: str):
    return Titles(
        common_fr=common_title_fr,
        specific_fr=specific_title_fr,
        common_en=common_title_en,
        specific_en=specific_title_en,
    )
