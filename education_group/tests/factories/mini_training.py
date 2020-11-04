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
import string

import factory.fuzzy

from base.models.enums import active_status, schedule_type as schedule_type_enum
from base.models.enums.education_group_types import MiniTrainingType
from education_group.ddd.domain.mini_training import MiniTraining, MiniTrainingIdentity
from education_group.tests.ddd.factories.campus import CampusIdentityFactory
from education_group.tests.ddd.factories.entity import EntityFactory
from education_group.tests.ddd.factories.titles import TitlesFactory


class MiniTrainingIdentityFactory(factory.Factory):
    class Meta:
        model = MiniTrainingIdentity
        abstract = False

    acronym = factory.Sequence(lambda n: 'Acronym%02d' % n)
    year = factory.fuzzy.FuzzyInteger(1999, 2099)


class MiniTrainingFactory(factory.Factory):
    class Meta:
        model = MiniTraining
        abstract = False

    entity_identity = factory.SubFactory(MiniTrainingIdentityFactory)
    entity_id = factory.LazyAttribute(lambda o: o.entity_identity)
    type = factory.Iterator(MiniTrainingType)
    code = factory.Sequence(lambda n: 'MiniCode%02d' % n)
    abbreviated_title = factory.fuzzy.FuzzyText(length=20, chars=string.ascii_uppercase)
    titles = factory.SubFactory(TitlesFactory)
    status = factory.Iterator(active_status.ActiveStatusEnum)
    schedule_type = factory.Iterator(schedule_type_enum.ScheduleTypeEnum)
    credits = factory.fuzzy.FuzzyInteger(60, 180)
    management_entity = factory.SubFactory(EntityFactory)
    start_year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)
    end_year = None
