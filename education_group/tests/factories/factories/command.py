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
import operator

import factory.fuzzy

from base.models.enums import education_group_types, schedule_type as schedule_type_enum, active_status, constraint_type
from education_group.ddd import command


class CreateOrphanMiniTrainingCommandFactory(factory.Factory):
    class Meta:
        model = command.CreateMiniTrainingCommand
        abstract = False

    code = "LOSIS2547"
    year = 2018
    type = factory.Iterator(education_group_types.MiniTrainingType.choices(), getter=operator.itemgetter(0))
    abbreviated_title = "Abbr title"
    title_fr = "Fr titre"
    title_en = "En title"
    status = factory.Iterator(active_status.ACTIVE_STATUS_LIST, getter=operator.itemgetter(0))
    schedule_type = factory.Iterator(schedule_type_enum.SCHEDULE_TYPES, getter=operator.itemgetter(0))
    credits = 30
    constraint_type = factory.Iterator(constraint_type.CONSTRAINT_TYPE, getter=operator.itemgetter(0))
    min_constraint = 1
    max_constraint = 10
    management_entity_acronym = "ACRON"
    teaching_campus_name = "LLN"
    organization_name = "ORG"
    remark_fr = ""
    remark_en = ""
    start_year = 2018
    end_year = None
    keywords = ""
