# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.db import transaction

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.funding_codes import FundingCodes
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.command import UpdateGroupCommand
from education_group.ddd.domain import training
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._co_graduation import CoGraduation
from education_group.ddd.domain._diploma import Diploma
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._funding import Funding
from education_group.ddd.domain._hops import HOPS
from education_group.ddd.domain._isced_domain import IscedDomain, IscedDomainIdentity
from education_group.ddd.domain._study_domain import StudyDomain, StudyDomainIdentity
from education_group.ddd.domain._titles import Titles
from education_group.ddd.repository import training as training_repository
from education_group.ddd.service.write import update_group_service


@transaction.atomic()
def update_training_and_group(cmd: command.UpdateTrainingAndGroupCommand) -> 'TrainingIdentity':
    errors = set()
    try:
        training_identity = training.TrainingIdentity(acronym=cmd.acronym, year=cmd.year)
        training_domain_obj = training_repository.TrainingRepository.get(training_identity)
        training_domain_obj.update(__convert_command_to_update_training_data(cmd))
        training_repository.TrainingRepository.update(training_domain_obj)
    except MultipleBusinessExceptions as e:
        errors = e.exceptions

    try:
        update_group_service.update_group(__convert_to_update_group_command(cmd))
    except MultipleBusinessExceptions as e:
        errors |= e.exceptions

    try:
        update_group_service.update_group(__convert_to_update_group_command(cmd))
    except MultipleBusinessExceptions as e:
        errors = e.exceptions

    if errors:
        raise MultipleBusinessExceptions(exceptions=errors)

    return training_identity


def __convert_command_to_update_training_data(cmd: command.UpdateTrainingAndGroupCommand) \
        -> 'training.UpdateTrainingData':
    return training.UpdateTrainingData(
        credits=cmd.credits,
        titles=Titles(
            title_fr=cmd.title_fr,
            partial_title_fr=cmd.partial_title_fr,
            title_en=cmd.title_en,
            partial_title_en=cmd.partial_title_en
        ),
        status=ActiveStatusEnum[cmd.status],
        duration=cmd.duration,
        duration_unit=DurationUnitsEnum[cmd.duration_unit] if cmd.duration_unit else None,
        keywords=cmd.keywords,
        internship_presence=InternshipPresence[cmd.internship_presence] if cmd.internship_presence else None,
        is_enrollment_enabled=cmd.is_enrollment_enabled,
        has_online_re_registration=cmd.has_online_re_registration,
        has_partial_deliberation=cmd.has_partial_deliberation,
        has_admission_exam=cmd.has_admission_exam,
        has_dissertation=cmd.has_dissertation,
        produce_university_certificate=cmd.produce_university_certificate,
        main_language=cmd.main_language,
        english_activities=ActivityPresence[cmd.english_activities] if cmd.english_activities else None,
        other_language_activities=ActivityPresence[cmd.other_language_activities]
        if cmd.other_language_activities else None,
        internal_comment=cmd.internal_comment,
        main_domain=StudyDomain(
            entity_id=StudyDomainIdentity(decree_name=cmd.main_domain_decree, code=cmd.main_domain_code),
            domain_name=None
        ) if cmd.main_domain_decree and cmd.main_domain_code else None,
        secondary_domains=[
            StudyDomain(
                entity_id=StudyDomainIdentity(decree_name=secondary_domain[0], code=secondary_domain[1]),
                domain_name=None
            ) for secondary_domain in (cmd.secondary_domains or [])],
        isced_domain=IscedDomain(
            entity_id=IscedDomainIdentity(code=cmd.isced_domain_code),
            title_fr=None,
            title_en=None
        ) if cmd.isced_domain_code else None,
        management_entity=Entity(acronym=cmd.management_entity_acronym),
        administration_entity=Entity(cmd.administration_entity_acronym),
        end_year=cmd.end_year,
        teaching_campus=Campus(name=cmd.teaching_campus_name, university_name=cmd.teaching_campus_organization_name),
        enrollment_campus=Campus(
            name=cmd.enrollment_campus_name,
            university_name=cmd.enrollment_campus_organization_name
        ),
        other_campus_activities=ActivityPresence[cmd.other_campus_activities]
        if cmd.other_campus_activities else None,
        funding=Funding(
            can_be_funded=cmd.can_be_funded,
            funding_orientation=FundingCodes[cmd.funding_orientation] if cmd.funding_orientation else None,
            can_be_international_funded=cmd.can_be_international_funded,
            international_funding_orientation=FundingCodes[cmd.international_funding_orientation]
            if cmd.international_funding_orientation else None
        ),
        hops=HOPS(
            ares_code=cmd.ares_code,
            ares_graca=cmd.ares_graca,
            ares_authorization=cmd.ares_authorization
        ) if cmd.ares_code or cmd.ares_graca or cmd.ares_authorization else None,
        co_graduation=CoGraduation(
            code_inter_cfb=cmd.code_inter_cfb,
            coefficient=cmd.coefficient
        ),
        diploma=Diploma(
            leads_to_diploma=cmd.leads_to_diploma,
            printing_title=cmd.printing_title,
            professional_title=cmd.professional_title,
            aims=None
        ),
        schedule_type=ScheduleTypeEnum[cmd.schedule_type],
        decree_category=DecreeCategories[cmd.decree_category] if cmd.decree_category else None,
        rate_code=RateCode[cmd.rate_code] if cmd.rate_code else None
    )


def __convert_to_update_group_command(training_command: command.UpdateTrainingAndGroupCommand) -> 'UpdateGroupCommand':
    return UpdateGroupCommand(
        code=training_command.code,
        year=training_command.year,
        abbreviated_title=training_command.acronym,
        title_fr=training_command.title_fr,
        title_en=training_command.title_en,
        credits=training_command.credits,
        constraint_type=training_command.constraint_type,
        min_constraint=training_command.min_constraint,
        max_constraint=training_command.max_constraint,
        management_entity_acronym=training_command.management_entity_acronym,
        teaching_campus_name=training_command.teaching_campus_name,
        organization_name=training_command.organization_name,
        remark_fr=training_command.remark_fr,
        remark_en=training_command.remark_en,
        end_year=training_command.end_year,
    )
