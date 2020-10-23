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

from base.models.enums.education_group_types import GroupType
from education_group.ddd.domain.group import GroupIdentity, Group
from education_group.tests.ddd.factories.campus import CampusIdentityFactory
from education_group.tests.ddd.factories.content_constraint import ContentConstraintFactory
from education_group.tests.ddd.factories.entity import EntityFactory
from education_group.tests.ddd.factories.remark import RemarkFactory
from education_group.tests.ddd.factories.titles import TitlesFactory


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
    credits = factory.fuzzy.FuzzyDecimal(0, 10, precision=1)
    content_constraint = factory.SubFactory(ContentConstraintFactory)
    management_entity = factory.SubFactory(EntityFactory)
    teaching_campus = factory.SubFactory(CampusIdentityFactory)
    remark = factory.SubFactory(RemarkFactory)
    start_year = factory.fuzzy.FuzzyInteger(1999, 2099)
    end_year = factory.LazyAttribute(generate_end_date)
