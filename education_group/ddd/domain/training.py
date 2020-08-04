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
from typing import List

import attr

from base.models.enums.academic_type import AcademicTypes
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.funding_codes import FundingCodes
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from base.models.utils import utils
from education_group.ddd.business_types import *
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._co_graduation import CoGraduation
from education_group.ddd.domain._co_organization import Coorganization
from education_group.ddd.domain._diploma import Diploma, DiplomaAim, DiplomaAimIdentity
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._funding import Funding
from education_group.ddd.domain._hops import HOPS
from education_group.ddd.domain._isced_domain import IscedDomain, IscedDomainIdentity
from education_group.ddd.domain._language import Language
from education_group.ddd.domain._study_domain import StudyDomain, StudyDomainIdentity
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain.exception import TrainingNotFoundException
from education_group.ddd.validators.validators_by_business_action import CreateTrainingValidatorList, \
    CopyTrainingValidatorList
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class TrainingIdentity(interface.EntityIdentity):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class TrainingIdentityThroughYears(interface.ValueObject):
    uuid = attr.ib(type=int)


class TrainingBuilder:

    def copy_to_next_year(self, training_from: 'Training', training_repository: 'TrainingRepository') -> 'Training':
        identity_next_year = TrainingIdentity(acronym=training_from.acronym, year=training_from.year + 1)
        try:
            training_next_year = training_repository.get(identity_next_year)
            # TODO :: Case update training next year - to implement in OSIS-4809
        except TrainingNotFoundException:
            # Case create training next year
            CopyTrainingValidatorList(training_from).validate()
            training_next_year = attr.evolve(  # Copy to new object
                training_from,
                entity_identity=identity_next_year,
                entity_id=identity_next_year,
            )
        return training_next_year

    def create_training(self, command: 'CreateTrainingCommand') -> 'Training':
        training_identity = TrainingIdentity(command.abbreviated_title, command.year)

        secondary_domains = []
        for dom in command.secondary_domains:
            secondary_domains.append(
                StudyDomain(
                    entity_id=StudyDomainIdentity(dom[0], dom[1]),
                    domain_name=None,
                )
            )

        command_aims = []
        for aim in command.aims:
            command_aims.append(
                DiplomaAim(
                    entity_id=DiplomaAimIdentity(code=aim[0], section=aim[1]),
                    description=None,
                )
            )

        training = Training(
            entity_identity=training_identity,
            entity_id=training_identity,
            type=utils.get_enum_from_str(command.type, TrainingType),
            credits=command.credits,
            schedule_type=utils.get_enum_from_str(command.schedule_type, ScheduleTypeEnum),
            duration=command.duration,
            duration_unit=utils.get_enum_from_str(command.duration_unit, DurationUnitsEnum),
            start_year=command.start_year,
            titles=Titles(
                title_fr=command.title_fr,
                partial_title_fr=command.partial_title_fr,
                title_en=command.title_en,
                partial_title_en=command.partial_title_en,
            ),
            status=utils.get_enum_from_str(command.status, ActiveStatusEnum),
            keywords=command.keywords,
            internship_presence=utils.get_enum_from_str(command.internship_presence, InternshipPresence),
            is_enrollment_enabled=command.is_enrollment_enabled,
            has_online_re_registration=command.has_online_re_registration,
            has_partial_deliberation=command.has_partial_deliberation,
            has_admission_exam=command.has_admission_exam,
            has_dissertation=command.has_dissertation,
            produce_university_certificate=command.produce_university_certificate,
            decree_category=utils.get_enum_from_str(command.decree_category, DecreeCategories),
            rate_code=utils.get_enum_from_str(command.rate_code, RateCode),
            main_language=Language(command.main_language) if command.main_language else None,
            english_activities=utils.get_enum_from_str(command.english_activities, ActivityPresence),
            other_language_activities=utils.get_enum_from_str(
                command.other_language_activities, ActivityPresence
            ),
            internal_comment=command.internal_comment,
            main_domain=StudyDomain(
                entity_id=StudyDomainIdentity(decree_name=command.main_domain_decree, code=command.main_domain_code),
                domain_name=None,
            ) if command.main_domain_code else None,
            secondary_domains=secondary_domains,
            isced_domain=IscedDomain(
                entity_id=IscedDomainIdentity(command.isced_domain_code),
                title_fr=None,
                title_en=None,
            ) if command.isced_domain_code else None,
            management_entity=Entity(acronym=command.management_entity_acronym),
            administration_entity=Entity(acronym=command.administration_entity_acronym),
            end_year=command.end_year,
            teaching_campus=Campus(
                name=command.teaching_campus_name,
                university_name=command.teaching_campus_organization_name,
            ),
            enrollment_campus=Campus(
                name=command.enrollment_campus_name,
                university_name=command.enrollment_campus_organization_name,
            ),
            other_campus_activities=utils.get_enum_from_str(command.other_campus_activities, ActivityPresence),
            funding=Funding(
                can_be_funded=command.can_be_funded,
                funding_orientation=FundingCodes[
                    command.funding_orientation
                ] if command.funding_orientation else None,
                can_be_international_funded=command.can_be_international_funded,
                international_funding_orientation=FundingCodes[
                    command.international_funding_orientation
                ] if command.international_funding_orientation else None,
            ),
            hops=HOPS(
                ares_code=command.ares_code,
                ares_graca=command.ares_graca,
                ares_authorization=command.ares_authorization,
            ) if all((command.ares_code, command.ares_graca, command.ares_authorization)) else None,
            co_graduation=CoGraduation(
                code_inter_cfb=command.code_inter_cfb,
                coefficient=command.coefficient,
            ),
            academic_type=utils.get_enum_from_str(command.academic_type, AcademicTypes),
            diploma=Diploma(
                leads_to_diploma=command.leads_to_diploma,
                printing_title=command.printing_title,
                professional_title=command.professional_title,
                aims=command_aims,
            ),
        )
        CreateTrainingValidatorList(training).validate()
        return training

    def _get_enum_from_str(self, value: str, enum_class):
        if not value:
            return None
        try:
            return enum_class[value]
        except ValueError:
            raise interface.BusinessException(
                "Invalid enum choice (value={}, enumeration_class={})".format(value, enum_class)
            )


@attr.s(slots=True)
class Training(interface.RootEntity):

    # FIXME :: split fields into separate ValueObjects (to discuss with business people)
    entity_id = entity_identity = attr.ib(type=TrainingIdentity)
    type = attr.ib(type=TrainingType)
    credits = attr.ib(type=int)
    start_year = attr.ib(type=int)
    titles = attr.ib(type=Titles)
    status = attr.ib(type=ActiveStatusEnum, default=ActiveStatusEnum.ACTIVE)
    identity_through_years = attr.ib(type=TrainingIdentityThroughYears, default=None)
    schedule_type = attr.ib(type=ScheduleTypeEnum, default=ScheduleTypeEnum.DAILY)
    duration = attr.ib(type=int, default=1)
    duration_unit = attr.ib(type=DurationUnitsEnum, default=DurationUnitsEnum.QUADRIMESTER)
    keywords = attr.ib(type=str, default="")
    internship_presence = attr.ib(type=InternshipPresence, default=InternshipPresence.NO)
    is_enrollment_enabled = attr.ib(type=bool, default=True)
    has_online_re_registration = attr.ib(type=bool, default=True)
    has_partial_deliberation = attr.ib(type=bool, default=False)
    has_admission_exam = attr.ib(type=bool, default=False)
    has_dissertation = attr.ib(type=bool, default=False)
    produce_university_certificate = attr.ib(type=bool, default=False)
    decree_category = attr.ib(type=DecreeCategories, default=None)
    rate_code = attr.ib(type=RateCode, default=None)
    main_language = attr.ib(type=Language, default=None)
    english_activities = attr.ib(type=ActivityPresence, default=None)
    other_language_activities = attr.ib(type=ActivityPresence, default=None)
    internal_comment = attr.ib(type=str, default=None)
    main_domain = attr.ib(type=StudyDomain, default=None)
    secondary_domains = attr.ib(type=List[StudyDomain], default=[])
    isced_domain = attr.ib(type=IscedDomain, default=None)
    management_entity = attr.ib(type=Entity, default=None)
    administration_entity = attr.ib(type=Entity, default=None)
    end_year = attr.ib(type=int, default=None)
    teaching_campus = attr.ib(type=Campus, default=None)
    enrollment_campus = attr.ib(type=Campus, default=None)
    other_campus_activities = attr.ib(type=ActivityPresence, default=None)
    funding = attr.ib(type=Funding, default=None)
    hops = attr.ib(type=HOPS, default=None)
    co_graduation = attr.ib(type=CoGraduation, default=None)
    co_organizations = attr.ib(type=List[Coorganization], factory=list)
    academic_type = attr.ib(type=AcademicTypes, default=None)
    diploma = attr.ib(type=Diploma, default=None)

    @property
    def acronym(self) -> str:
        return self.entity_id.acronym

    @property
    def year(self) -> int:
        return self.entity_id.year

    def is_finality(self) -> bool:
        return self.type in set(TrainingType.finality_types_enum())

    def is_bachelor(self) -> bool:
        return self.type == TrainingType.BACHELOR

    def is_master_specialized(self):
        return self.type == TrainingType.MASTER_MC

    def is_aggregation(self):
        return self.type == TrainingType.AGGREGATION

    def is_master_60_credits(self):
        return self.type == TrainingType.MASTER_M1

    def is_master_120_credits(self):
        return self.type == TrainingType.PGRM_MASTER_120

    def is_master_180_240_credits(self):
        return self.type == TrainingType.PGRM_MASTER_180_240
