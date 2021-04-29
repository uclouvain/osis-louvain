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

from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain.exception import TrainingCopyConsistencyException
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.service.write import postpone_training_and_group_modification_service, \
    update_training_and_group_service
from program_management.ddd.command import PostponeProgramTreeVersionCommand, \
    PostponeProgramTreeCommand, PostponeTrainingAndRootGroupModificationWithProgramTreeCommand, \
    UpdateProgramTreeVersionEndDateCommand
from program_management.ddd.domain.program_tree_version import STANDARD, NOT_A_TRANSITION
from program_management.ddd.domain.service.is_academic_year_in_past import IsAcademicYearInPast
from program_management.ddd.service.write import postpone_tree_specific_version_service, \
    postpone_program_tree_service, update_program_tree_version_end_date_service


def postpone_training_and_program_tree_modifications(
        update_command: PostponeTrainingAndRootGroupModificationWithProgramTreeCommand,
        academic_year_repository: 'IAcademicYearRepository',
        training_repository: 'TrainingRepository'
) -> List['TrainingIdentity']:
    is_in_past = IsAcademicYearInPast().is_in_past(update_command.postpone_from_year, academic_year_repository)
    training_identity = TrainingIdentity(
        acronym=update_command.postpone_from_acronym,
        year=update_command.postpone_from_year
    )
    training_domain_obj = training_repository.get(training_identity)
    has_end_year_changed = training_domain_obj.end_year != update_command.end_year

    update_program_tree_version_end_date_service.update_program_tree_version_end_date(
        __convert_to_update_program_tree_version_end_date_command(update_command)
    )
    postpone_cmd = __convert_to_postpone_training_and_group_modification_command(update_command)
    if not is_in_past or has_end_year_changed:
        consistency_error = None
        try:
            training_identities = \
                postpone_training_and_group_modification_service.postpone_training_and_group_modification(
                    postpone_cmd
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
    else:
        training_identities = [
            update_training_and_group_service.update_training_and_group(
                __convert_to_update_training_and_group_command(postpone_cmd)
            )
        ]

    return training_identities


def __convert_to_update_training_and_group_command(
        postpone_cmd: command.PostponeTrainingAndGroupModificationCommand
) -> command.UpdateTrainingAndGroupCommand:
    return command.UpdateTrainingAndGroupCommand(
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
