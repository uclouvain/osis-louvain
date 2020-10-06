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

from django.db import transaction

from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain.training import TrainingBuilder
from education_group.ddd.repository import training as training_repository
from education_group.ddd.service.write import postpone_training_and_group_modification_service, create_group_service


@transaction.atomic()
def create_and_postpone_orphan_training(create_training_cmd: command.CreateTrainingCommand) -> List['TrainingIdentity']:
    # GIVEN
    cmd = create_training_cmd

    # WHEN
    training = TrainingBuilder().create_training(cmd)
    group_identity = create_group_service.create_orphan_group(__convert_to_create_group_command(create_training_cmd))

    # THEN
    training_id = training_repository.TrainingRepository.create(training)
    training_identities = postpone_training_and_group_modification_service.postpone_training_and_group_modification(
        command.PostponeTrainingAndGroupModificationCommand(
            postpone_from_acronym=training_id.acronym,
            postpone_from_year=training_id.year,

            code=cmd.code,
            status=cmd.status,
            credits=cmd.credits,
            duration=cmd.duration,
            title_fr=cmd.title_fr,
            partial_title_fr=cmd.partial_title_fr,
            title_en=cmd.title_en,
            partial_title_en=cmd.partial_title_en,
            keywords=cmd.keywords,
            internship_presence=cmd.internship_presence,
            is_enrollment_enabled=cmd.is_enrollment_enabled,
            has_online_re_registration=cmd.has_online_re_registration,
            has_partial_deliberation=cmd.has_partial_deliberation,
            has_admission_exam=cmd.has_admission_exam,
            has_dissertation=cmd.has_dissertation,
            produce_university_certificate=cmd.produce_university_certificate,
            main_language=cmd.main_language,
            english_activities=cmd.english_activities,
            other_language_activities=cmd.other_language_activities,
            internal_comment=cmd.internal_comment,
            main_domain_code=cmd.main_domain_code,
            main_domain_decree=cmd.main_domain_decree,
            secondary_domains=cmd.secondary_domains,
            isced_domain_code=cmd.isced_domain_code,
            management_entity_acronym=cmd.management_entity_acronym,
            administration_entity_acronym=cmd.administration_entity_acronym,
            end_year=cmd.end_year,
            teaching_campus_name=cmd.teaching_campus_name,
            teaching_campus_organization_name=cmd.teaching_campus_organization_name,
            enrollment_campus_name=cmd.enrollment_campus_name,
            enrollment_campus_organization_name=cmd.enrollment_campus_organization_name,
            other_campus_activities=cmd.other_campus_activities,
            can_be_funded=cmd.can_be_funded,
            funding_orientation=cmd.funding_orientation,
            can_be_international_funded=cmd.can_be_international_funded,
            international_funding_orientation=cmd.international_funding_orientation,
            ares_code=cmd.ares_code,
            ares_graca=cmd.ares_graca,
            ares_authorization=cmd.ares_authorization,
            code_inter_cfb=cmd.code_inter_cfb,
            coefficient=cmd.coefficient,
            duration_unit=cmd.duration_unit,
            leads_to_diploma=cmd.leads_to_diploma,
            printing_title=cmd.printing_title,
            professional_title=cmd.professional_title,
            constraint_type=cmd.constraint_type,
            min_constraint=cmd.min_constraint,
            max_constraint=cmd.max_constraint,
            remark_fr=cmd.remark_fr,
            remark_en=cmd.remark_en,
            organization_name=cmd.teaching_campus_organization_name,
            schedule_type=cmd.schedule_type,
        )
    )

    return training_identities


def __convert_to_create_group_command(cmd: command.CreateTrainingCommand) -> command.CreateOrphanGroupCommand:
    return command.CreateOrphanGroupCommand(
        code=cmd.code,
        year=cmd.year,
        type=cmd.type,
        abbreviated_title=cmd.abbreviated_title,
        title_fr=cmd.title_fr,
        title_en=cmd.title_en,
        credits=cmd.credits,
        constraint_type=cmd.constraint_type,
        min_constraint=cmd.min_constraint,
        max_constraint=cmd.max_constraint,
        management_entity_acronym=cmd.management_entity_acronym,
        teaching_campus_name=cmd.teaching_campus_name,
        organization_name=cmd.teaching_campus_organization_name,
        remark_fr=cmd.remark_fr,
        remark_en=cmd.remark_en,
        start_year=cmd.start_year,
        end_year=cmd.end_year,
    )
