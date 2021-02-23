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
from education_group.ddd.business_types import *
from education_group.ddd.domain.exception import TrainingCopyConsistencyException
from education_group.ddd.service.write import postpone_training_and_group_modification_service
from program_management.ddd.command import PostponeProgramTreeVersionCommand, \
    PostponeProgramTreeCommand, PostponeTrainingAndRootGroupModificationWithProgramTreeCommand, \
    UpdateProgramTreeVersionEndDateCommand
from program_management.ddd.domain.program_tree_version import STANDARD, NOT_A_TRANSITION
from program_management.ddd.service.write import postpone_tree_specific_version_service, \
    postpone_program_tree_service, update_program_tree_version_end_date_service


def postpone_training_and_program_tree_modifications(
        update_command: PostponeTrainingAndRootGroupModificationWithProgramTreeCommand
) -> List['TrainingIdentity']:
    update_program_tree_version_end_date_service.update_program_tree_version_end_date(
        __convert_to_update_program_tree_version_end_date_command(update_command)
    )

    consistency_error = None
    try:
        training_identities = postpone_training_and_group_modification_service.postpone_training_and_group_modification(
            __convert_to_postpone_training_and_group_modification_command(update_command)
        )
    except TrainingCopyConsistencyException as e:
        consistency_error = e

    postpone_program_tree_service.postpone_program_tree(
        PostponeProgramTreeCommand(
            from_code=update_command.code,
            from_year=update_command.postpone_from_year,
            offer_acronym=update_command.postpone_from_acronym
        )
    )

    postpone_tree_specific_version_service.postpone_program_tree_version(
        PostponeProgramTreeVersionCommand(
            from_offer_acronym=update_command.postpone_from_acronym,
            from_version_name=STANDARD,
            from_year=update_command.postpone_from_year,
            from_transition_name=NOT_A_TRANSITION
        )
    )
    if consistency_error:
        raise consistency_error
    return training_identities


def __convert_to_postpone_training_and_group_modification_command(
    cmd: PostponeTrainingAndRootGroupModificationWithProgramTreeCommand
) -> command.PostponeTrainingAndGroupModificationCommand:
    return command.PostponeTrainingAndGroupModificationCommand(
        postpone_from_acronym=cmd.postpone_from_acronym,
        postpone_from_year=cmd.postpone_from_year,
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
        organization_name=cmd.organization_name,
        schedule_type=cmd.schedule_type,
        decree_category=cmd.decree_category,
        rate_code=cmd.rate_code
    )


def __convert_to_update_program_tree_version_end_date_command(
        cmd: PostponeTrainingAndRootGroupModificationWithProgramTreeCommand
) -> UpdateProgramTreeVersionEndDateCommand:
    return UpdateProgramTreeVersionEndDateCommand(
        from_offer_acronym=cmd.postpone_from_acronym,
        from_version_name="",
        from_year=cmd.postpone_from_year,
        from_transition_name=NOT_A_TRANSITION,
        end_date=cmd.end_year
    )
