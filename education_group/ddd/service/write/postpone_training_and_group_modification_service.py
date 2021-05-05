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

from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.repository import training as training_repository
from education_group.ddd.service.write import copy_training_service, update_training_and_group_service, \
    copy_group_service
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement


def postpone_training_and_group_modification(postpone_cmd: command.PostponeTrainingAndGroupModificationCommand) \
        -> List['TrainingIdentity']:
    # GIVEN
    from_training_id = TrainingIdentity(
        acronym=postpone_cmd.postpone_from_acronym,
        year=postpone_cmd.postpone_from_year
    )
    conflicted_fields = ConflictedFields().get_training_conflicted_fields(from_training_id)

    # WHEN
    identities_created = [
        update_training_and_group_service.update_training_and_group(
            command.UpdateTrainingAndGroupCommand(
                acronym=postpone_cmd.postpone_from_acronym,
                code=postpone_cmd.code,
                year=postpone_cmd.postpone_from_year,
                status=postpone_cmd.status,
                credits=postpone_cmd.credits,
                duration=postpone_cmd.duration,
                title_fr=postpone_cmd.title_fr,
                partial_title_fr=postpone_cmd.partial_title_fr,
                title_en=postpone_cmd.title_en,
                partial_title_en=postpone_cmd.partial_title_en,
                keywords=postpone_cmd.keywords,
                internship_presence=postpone_cmd.internship_presence,
                is_enrollment_enabled=postpone_cmd.is_enrollment_enabled,
                has_online_re_registration=postpone_cmd.has_online_re_registration,
                has_partial_deliberation=postpone_cmd.has_partial_deliberation,
                has_admission_exam=postpone_cmd.has_admission_exam,
                has_dissertation=postpone_cmd.has_dissertation,
                produce_university_certificate=postpone_cmd.produce_university_certificate,
                main_language=postpone_cmd.main_language,
                english_activities=postpone_cmd.english_activities,
                other_language_activities=postpone_cmd.other_language_activities,
                internal_comment=postpone_cmd.internal_comment,
                main_domain_code=postpone_cmd.main_domain_code,
                main_domain_decree=postpone_cmd.main_domain_decree,
                secondary_domains=postpone_cmd.secondary_domains,
                isced_domain_code=postpone_cmd.isced_domain_code,
                management_entity_acronym=postpone_cmd.management_entity_acronym,
                administration_entity_acronym=postpone_cmd.administration_entity_acronym,
                end_year=postpone_cmd.end_year,
                teaching_campus_name=postpone_cmd.teaching_campus_name,
                teaching_campus_organization_name=postpone_cmd.teaching_campus_organization_name,
                enrollment_campus_name=postpone_cmd.enrollment_campus_name,
                enrollment_campus_organization_name=postpone_cmd.enrollment_campus_organization_name,
                other_campus_activities=postpone_cmd.other_campus_activities,
                can_be_funded=postpone_cmd.can_be_funded,
                funding_orientation=postpone_cmd.funding_orientation,
                can_be_international_funded=postpone_cmd.can_be_international_funded,
                international_funding_orientation=postpone_cmd.international_funding_orientation,
                ares_code=postpone_cmd.ares_code,
                ares_graca=postpone_cmd.ares_graca,
                ares_authorization=postpone_cmd.ares_authorization,
                code_inter_cfb=postpone_cmd.code_inter_cfb,
                coefficient=postpone_cmd.coefficient,
                duration_unit=postpone_cmd.duration_unit,
                leads_to_diploma=postpone_cmd.leads_to_diploma,
                printing_title=postpone_cmd.printing_title,
                professional_title=postpone_cmd.professional_title,
                constraint_type=postpone_cmd.constraint_type,
                min_constraint=postpone_cmd.min_constraint,
                max_constraint=postpone_cmd.max_constraint,
                remark_fr=postpone_cmd.remark_fr,
                remark_en=postpone_cmd.remark_en,
                organization_name=postpone_cmd.organization_name,
                schedule_type=postpone_cmd.schedule_type,
                decree_category=postpone_cmd.decree_category,
                rate_code=postpone_cmd.rate_code
            )
        )
    ]
    end_postponement_year = CalculateEndPostponement.calculate_end_postponement_year_training(
        identity=from_training_id,
        repository=training_repository.TrainingRepository()
    )
    for year in range(from_training_id.year, end_postponement_year):
        if year + 1 in conflicted_fields:
            continue  # Do not copy info from year to N+1 because conflict detected

        identity_next_year = copy_training_service.copy_training_to_next_year(
            copy_cmd=command.CopyTrainingToNextYearCommand(
                acronym=postpone_cmd.postpone_from_acronym,
                postpone_from_year=year
            )
        )
        copy_group_service.copy_group(
            cmd=command.CopyGroupCommand(
                from_code=postpone_cmd.code,
                from_year=year
            )
        )
        # THEN
        identities_created.append(identity_next_year)
    if conflicted_fields:
        first_conflict_year = min(conflicted_fields.keys())
        raise exception.TrainingCopyConsistencyException(first_conflict_year, conflicted_fields[first_conflict_year])
    return identities_created
