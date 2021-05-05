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
from typing import List

import factory.fuzzy

from base.models.enums import active_status, schedule_type as schedule_type_enum
from base.models.enums.education_group_types import MiniTrainingType
from education_group.ddd import command
from education_group.ddd.domain.mini_training import MiniTraining, MiniTrainingIdentity
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.service.write import copy_mini_training_service
from education_group.tests.ddd.factories.entity import EntityFactory
from education_group.tests.ddd.factories.titles import TitlesFactory
from program_management.ddd.domain.node import Node, NodeGroupYear


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

    @factory.post_generation
    def persist(obj, create, extracted, **kwargs):
        if extracted:
            mini_training_repository.MiniTrainingRepository.create(obj)

    @classmethod
    def multiple(cls, n, *args, **kwargs) -> List['MiniTraining']:
        first_mini_training = cls(*args, **kwargs)  # type: MiniTraining

        result = [first_mini_training]
        for year in range(first_mini_training.year, first_mini_training.year + n - 1):
            identity = copy_mini_training_service.copy_mini_training_to_next_year(
                command.CopyMiniTrainingToNextYearCommand(acronym=first_mini_training.acronym, postpone_from_year=year)
            )
            result.append(mini_training_repository.MiniTrainingRepository.get(identity))

        return result

    @classmethod
    def from_node(cls, node: 'NodeGroupYear') -> MiniTraining:
        return cls(
            code=node.code,
            type=node.node_type,
            entity_identity__acronym=node.title,
            entity_identity__year=node.year,
            start_year=node.start_year,
            end_year=node.end_date,
            abbreviated_title=node.title,
            management_entity__acronym=node.management_entity_acronym,
            credits=node.credits,
            schedule_type=node.schedule_type,
            titles__title_fr=node.offer_title_fr,
            titles__title_en=node.offer_title_en,
            titles__partial_title_fr=node.offer_partial_title_fr,
            titles__partial_title_en=node.offer_partial_title_en,
            status=node.offer_status
        )


