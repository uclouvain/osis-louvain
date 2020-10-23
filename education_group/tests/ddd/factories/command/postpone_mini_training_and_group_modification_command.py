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
import factory.fuzzy

from base.models.enums import education_group_types
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd import command


class PostponeMiniTrainingAndGroupModificationCommandFactory(factory.Factory):
    class Meta:
        model = command.PostponeMiniTrainingAndGroupModificationCommand
        abstract = False

    postpone_from_abbreviated_title = "Title "
    postpone_from_year = 2019

    status = ActiveStatusEnum.ACTIVE.name
    code = "Code"
    credits = 23
    schedule_type = ScheduleTypeEnum.DAILY.name
    end_year = None
    title_fr = "fr  title"
    title_en = "title  en"
    teaching_campus_name = None
    management_entity_acronym = None
    organization_name = None
    constraint_type = None
    min_constraint = None
    max_constraint = None
    remark_fr = None
    remark_en = None
    keywords = ""
