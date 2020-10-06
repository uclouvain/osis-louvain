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
import operator

import factory.fuzzy

from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command


class CreateAndPostponeTrainingAndProgramTreeCommandFactory(factory.Factory):
    class Meta:
        model = command.CreateTrainingCommand
        abstract = False

    abbreviated_title = factory.Sequence(lambda n: 'TrainingTitle%d' % n)
    status = factory.Iterator(ActiveStatusEnum.choices(), getter=operator.itemgetter(0))
    code = factory.Sequence(lambda n: 'CODE%d' % n)
    year = 2019
    type = factory.Iterator(TrainingType.choices(), getter=operator.itemgetter(0))
    credits = 23
    schedule_type = ScheduleTypeEnum.DAILY.name
    duration = 3
    start_year = 2019
    title_fr = "fr  title "
    title_en = "title  en "
    partial_title_fr = None
    partial_title_en = None
    keywords = ""
    internship_presence = None
    is_enrollment_enabled = False
    has_online_re_registration = False
    has_partial_deliberation = False
    has_admission_exam = False
    has_dissertation = False
    produce_university_certificate = True
    decree_category = None
    rate_code = None
    main_language = 'French'
    english_activities = None
    other_language_activities = None
    internal_comment = ""
    main_domain_code = None
    main_domain_decree = None
    secondary_domains = []
    isced_domain_code = None
    management_entity_acronym = factory.Sequence(lambda n: 'ENTITY%d' % n)
    administration_entity_acronym = factory.SelfAttribute("management_entity_acronym")
    end_year = None
    teaching_campus_name = factory.Sequence(lambda n: 'TeachingCampus%d' % n)
    teaching_campus_organization_name = factory.Sequence(lambda n: 'TeachingOrganization%d' % n)
    enrollment_campus_name = factory.SelfAttribute("teaching_campus_name")
    enrollment_campus_organization_name = factory.SelfAttribute("teaching_campus_organization_name")
    other_campus_activities = None
    funding_orientation = None
    can_be_international_funded = True
    international_funding_orientation = None
    ares_code = None
    ares_graca = None
    ares_authorization = None
    code_inter_cfb = None
    coefficient = None
    academic_type = None
    duration_unit = None
    leads_to_diploma = True
    printing_title = ''
    professional_title = ''
    constraint_type = None
    min_constraint = None
    max_constraint = None
    remark_fr = None
    remark_en = None
    can_be_funded = True
