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
from typing import List

from base.models.enums.academic_type import AcademicTypes
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._co_graduation import CoGraduation
from education_group.ddd.domain._co_organization import Coorganization
from education_group.ddd.domain._diploma import Diploma
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._funding import Funding
from education_group.ddd.domain._hops import HOPS
from education_group.ddd.domain._isced_domain import IscedDomain
from education_group.ddd.domain._language import Language
from education_group.ddd.domain._study_domain import StudyDomain
from education_group.ddd.domain._titles import Titles
from osis_common.ddd import interface


class TrainingIdentity(interface.EntityIdentity):
    def __init__(self, acronym: str, year: int):
        self.acronym = acronym
        self.year = year

    def __hash__(self):
        return hash(self.acronym + str(self.year))

    def __eq__(self, other):
        return self.acronym == other.acronym and self.year == other.year


class Training(interface.RootEntity):

    # FIXME :: split into ValueObjects (to discuss with business people)
    def __init__(
            self,
            entity_identity: 'TrainingIdentity',
            type: TrainingType,
            credits: Decimal,
            schedule_type: ScheduleTypeEnum,
            duration: int,
            start_year: int,
            titles: Titles,
            keywords: str = None,
            internship: InternshipPresence = None,
            is_enrollment_enabled: bool = True,
            has_online_re_registration: bool = True,
            has_partial_deliberation: bool = False,
            has_admission_exam: bool = False,
            has_dissertation: bool = False,
            produce_university_certificate: bool = False,
            decree_category: DecreeCategories = None,
            rate_code: RateCode = None,
            main_language: Language = None,
            english_activities: ActivityPresence = None,
            other_language_activities: ActivityPresence = None,
            internal_comment: str = None,
            main_domain: StudyDomain = None,
            secondary_domains: List[StudyDomain] = None,
            isced_domain: IscedDomain = None,
            management_entity: Entity = None,
            administration_entity: Entity = None,
            end_year: int = None,
            teaching_campus: Campus = None,
            enrollment_campus: Campus = None,
            other_campus_activities: ActivityPresence = None,
            funding: Funding = None,
            hops: HOPS = None,
            co_graduation: CoGraduation = None,
            co_organizations: List[Coorganization] = None,
            academic_type: AcademicTypes = None,
            duration_unit: DurationUnitsEnum = None,
            diploma: Diploma = None,
    ):
        super(Training, self).__init__(entity_id=entity_identity)
        self.entity_id = entity_identity
        self.type = type
        self.credits = credits
        self.schedule_type = schedule_type
        self.duration = duration
        self.duration_unit = duration_unit or DurationUnitsEnum.QUADRIMESTER
        self.start_year = start_year
        self.titles = titles
        self.keywords = keywords
        self.internship = internship
        self.is_enrollment_enabled = is_enrollment_enabled or True
        self.has_online_re_registration = has_online_re_registration or True
        self.has_partial_deliberation = has_partial_deliberation or False
        self.has_admission_exam = has_admission_exam or False
        self.has_dissertation = has_dissertation or False
        self.produce_university_certificate = produce_university_certificate or False
        self.decree_category = decree_category
        self.rate_code = rate_code
        self.main_language = main_language
        self.english_activities = english_activities
        self.other_language_activities = other_language_activities
        self.internal_comment = internal_comment
        self.main_domain = main_domain
        self.secondary_domains = secondary_domains
        self.isced_domain = isced_domain
        self.management_entity = management_entity
        self.administration_entity = administration_entity
        self.end_year = end_year
        self.teaching_campus = teaching_campus
        self.enrollment_campus = enrollment_campus
        self.other_campus_activities = other_campus_activities
        self.funding = funding
        self.hops = hops
        self.co_graduation = co_graduation
        self.co_organizations = co_organizations
        self.academic_type = academic_type
        self.diploma = diploma

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
