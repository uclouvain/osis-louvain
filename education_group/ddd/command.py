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
from _decimal import Decimal
from typing import List, Tuple, Optional

import attr

from osis_common.ddd import interface

DecreeName = str
DomainCode = str
CampusName = str
UniversityName = str
PartnerName = str
AimCode = int
AimSection = int


@attr.s(frozen=True, slots=True)
class CreateTrainingCommand(interface.CommandRequest):

    abbreviated_title = attr.ib(type=str)
    status = attr.ib(type=str)
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    credits = attr.ib(type=int)
    schedule_type = attr.ib(type=str)
    duration = attr.ib(type=int)
    start_year = attr.ib(type=int)

    title_fr = attr.ib(type=str)
    partial_title_fr = attr.ib(type=Optional[str])
    title_en = attr.ib(type=Optional[str])
    partial_title_en = attr.ib(type=Optional[str])

    keywords = attr.ib(type=Optional[str])
    internship_presence = attr.ib(type=Optional[str])
    is_enrollment_enabled = attr.ib(type=Optional[bool])
    has_online_re_registration = attr.ib(type=Optional[bool])
    has_partial_deliberation = attr.ib(type=Optional[bool])
    has_admission_exam = attr.ib(type=Optional[bool])
    has_dissertation = attr.ib(type=Optional[bool])
    produce_university_certificate = attr.ib(type=Optional[bool])
    decree_category = attr.ib(type=Optional[str])
    rate_code = attr.ib(type=Optional[str])
    main_language = attr.ib(type=Optional[str])
    english_activities = attr.ib(type=Optional[str])
    other_language_activities = attr.ib(type=Optional[str])
    internal_comment = attr.ib(type=Optional[str])
    main_domain_code = attr.ib(type=Optional[str])
    main_domain_decree = attr.ib(type=Optional[str])

    secondary_domains = attr.ib(type=Optional[List[Tuple[DecreeName, DomainCode]]])

    isced_domain_code = attr.ib(type=Optional[str])
    management_entity_acronym = attr.ib(type=Optional[str])
    administration_entity_acronym = attr.ib(type=Optional[str])
    end_year = attr.ib(type=Optional[int])

    teaching_campus_name = attr.ib(type=Optional[str])
    teaching_campus_organization_name = attr.ib(type=Optional[str])

    enrollment_campus_name = attr.ib(type=Optional[str])
    enrollment_campus_organization_name = attr.ib(type=Optional[str])

    other_campus_activities = attr.ib(type=Optional[str])

    can_be_funded = attr.ib(type=Optional[bool])
    funding_orientation = attr.ib(type=Optional[str])
    can_be_international_funded = attr.ib(type=Optional[bool])
    international_funding_orientation = attr.ib(type=Optional[str])

    ares_code = attr.ib(type=Optional[int])
    ares_graca = attr.ib(type=Optional[int])
    ares_authorization = attr.ib(type=Optional[int])

    code_inter_cfb = attr.ib(type=Optional[str])
    coefficient = attr.ib(type=Optional[Decimal])

    academic_type = attr.ib(type=Optional[str])
    duration_unit = attr.ib(type=Optional[str])

    leads_to_diploma = attr.ib(type=Optional[bool])
    printing_title = attr.ib(type=Optional[str])
    professional_title = attr.ib(type=Optional[str])
    aims = attr.ib(type=Optional[List[Tuple[AimCode, AimSection]]])

    constraint_type = attr.ib(type=Optional[str])
    min_constraint = attr.ib(type=Optional[int])
    max_constraint = attr.ib(type=Optional[int])
    remark_fr = attr.ib(type=Optional[str])
    remark_en = attr.ib(type=Optional[str])


@attr.s(frozen=True, slots=True)
class GetGroupCommand(interface.CommandRequest):

    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class GetMiniTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class CreateMiniTrainingCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    abbreviated_title = attr.ib(type=str)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    keywords = attr.ib(type=str)
    status = attr.ib(type=str)
    schedule_type = attr.ib(type=str)
    credits = attr.ib(type=int)
    constraint_type = attr.ib(type=str)
    min_constraint = attr.ib(type=int)
    max_constraint = attr.ib(type=int)
    management_entity_acronym = attr.ib(type=str)
    teaching_campus_name = attr.ib(type=str)
    organization_name = attr.ib(type=str)
    remark_fr = attr.ib(type=str)
    remark_en = attr.ib(type=str)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int])


@attr.s(frozen=True, slots=True)
class CreateOrphanGroupCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    abbreviated_title = attr.ib(type=str)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    constraint_type = attr.ib(type=str)
    min_constraint = attr.ib(type=int)
    max_constraint = attr.ib(type=int)
    management_entity_acronym = attr.ib(type=str)
    teaching_campus_name = attr.ib(type=str)
    organization_name = attr.ib(type=str)
    remark_fr = attr.ib(type=str)
    remark_en = attr.ib(type=str)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int])


@attr.s(frozen=True, slots=True)
class CopyGroupCommand(interface.CommandRequest):
    from_code = attr.ib(type=str)
    from_year = attr.ib(type=int)
    to_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class UpdateGroupCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    abbreviated_title = attr.ib(type=str)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    constraint_type = attr.ib(type=str)
    min_constraint = attr.ib(type=int)
    max_constraint = attr.ib(type=int)
    management_entity_acronym = attr.ib(type=str)
    teaching_campus_name = attr.ib(type=str)
    organization_name = attr.ib(type=str)
    remark_fr = attr.ib(type=str)
    remark_en = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class PostponeTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    postpone_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class PostponeMiniTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    postpone_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class CopyTrainingToNextYearCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    postpone_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class CopyMiniTrainingToNextYearCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    postpone_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class DeleteOrphanGroupCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class DeleteOrphanTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class DeleteOrphanMiniTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class GetTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class GetMiniTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)
