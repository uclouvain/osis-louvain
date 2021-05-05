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

import factory.fuzzy

from base.models.enums.education_group_types import GroupType
from education_group.ddd import command
from education_group.ddd.domain.group import GroupIdentity, Group
from education_group.ddd.repository import group as group_repository
from education_group.ddd.service.write import copy_group_service
from education_group.tests.ddd.factories.campus import CampusFactory
from education_group.tests.ddd.factories.content_constraint import ContentConstraintFactory
from education_group.tests.ddd.factories.entity import EntityFactory
from education_group.tests.ddd.factories.remark import RemarkFactory
from education_group.tests.ddd.factories.titles import TitlesFactory
from program_management.ddd.domain.node import Node, NodeGroupYear
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion


def generate_end_date(group):
    return group.entity_identity.year + 10


class GroupIdentityFactory(factory.Factory):
    class Meta:
        model = GroupIdentity
        abstract = False

    code = factory.Sequence(lambda n: 'Code%02d' % n)
    year = factory.fuzzy.FuzzyInteger(1999, 2099)


class GroupFactory(factory.Factory):
    class Meta:
        model = Group
        abstract = False

    entity_identity = factory.SubFactory(GroupIdentityFactory)
    entity_id = factory.LazyAttribute(lambda o: o.entity_identity)
    type = factory.fuzzy.FuzzyChoice(GroupType)
    abbreviated_title = factory.Sequence(lambda n: "Acronym%02d" % n)
    titles = factory.SubFactory(TitlesFactory)
    credits = factory.fuzzy.FuzzyInteger(0, 10)
    content_constraint = factory.SubFactory(ContentConstraintFactory)
    management_entity = factory.SubFactory(EntityFactory)
    teaching_campus = factory.SubFactory(CampusFactory)
    remark = factory.SubFactory(RemarkFactory)
    start_year = factory.fuzzy.FuzzyInteger(1999, 2099)
    end_year = factory.LazyAttribute(generate_end_date)

    @factory.post_generation
    def persist(obj, create, extracted, **kwargs):
        if extracted:
            group_repository.GroupRepository.create(obj)

    @classmethod
    def multiple(cls, n, *args, **kwargs) -> List['Group']:
        first_group = cls(*args, **kwargs)  # type: Group

        result = [first_group]
        for year in range(first_group.year, first_group.year + n - 1):
            identity = copy_group_service.copy_group(
                command.CopyGroupCommand(from_code=first_group.code, from_year=year)
            )
            result.append(group_repository.GroupRepository.get(identity))

        return result

    @classmethod
    def from_node(cls, node: 'NodeGroupYear') -> Group:
        return cls(
            abbreviated_title=node.title,
            type=node.node_type,
            entity_identity__code=node.code,
            entity_identity__year=node.year,
            start_year=node.start_year,
            end_year=node.end_date,
            management_entity__acronym=node.management_entity_acronym,
            teaching_campus__name=node.teaching_campus.name,
            teaching_campus__university_name='OSIS',
            content_constraint__type=node.constraint_type,
            content_constraint__minimum=node.min_constraint,
            content_constraint__maximum=node.max_constraint,
            credits=node.credits,
            titles__title_fr=node.offer_title_fr,
            titles__title_en=node.offer_title_en,
            titles__partial_title_fr=node.offer_partial_title_fr,
            titles__partial_title_en=node.offer_partial_title_en,
        )


