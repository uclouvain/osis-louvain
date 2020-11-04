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
import random

import factory.fuzzy

from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._entity import Entity as EntityValueObject
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain.group import Group, GroupIdentity


def generate_group_identity(group: 'Group') -> '':
    sigle_ele = "".join(random.sample(string.ascii_uppercase, k=5))
    cnum = "".join(random.sample(string.digits, k=3))
    subdivision = random.choice(string.ascii_uppercase)
    code = "{sigle_ele}{cnum}{subdivision}".format(
        sigle_ele=sigle_ele,
        cnum=cnum,
        subdivision=subdivision
    )
    return GroupIdentity(code=code, year=group.start_year)


def generate_titles(group: 'Group') -> 'Titles':
    return Titles(
        title_fr=factory.fuzzy.FuzzyText(length=120).fuzz(),
        title_en=factory.fuzzy.FuzzyText(length=120).fuzz(),
    )


def generate_content_constraint(group: 'Group') -> 'ContentConstraint':
    return ContentConstraint(
        type=ConstraintTypeEnum.CREDITS,
        minimum=factory.fuzzy.FuzzyInteger(low=0, high=10).fuzz(),
        maximum=factory.fuzzy.FuzzyInteger(low=11, high=180).fuzz()
    )


def generate_management_entity(group: 'Group') -> 'EntityValueObject':
    management_acronym = "".join(random.sample(string.ascii_uppercase, k=4))
    return EntityValueObject(acronym=management_acronym)


def generate_teaching_campus(group: 'Group') -> 'Campus':
    return Campus(
        name=factory.fuzzy.FuzzyText(length=20).fuzz(),
        university_name=factory.fuzzy.FuzzyText(length=20).fuzz(),
    )


def generate_remark(group: 'Group') -> 'Remark':
    return Remark(
        text_fr=factory.fuzzy.FuzzyText(length=120).fuzz(),
        text_en=factory.fuzzy.FuzzyText(length=120).fuzz()
    )


class GroupFactory(factory.Factory):
    class Meta:
        model = Group
        abstract = False

    entity_identity = factory.LazyAttribute(generate_group_identity)
    entity_id = factory.LazyAttribute(lambda o: o.entity_identity)
    type = GroupType.COMMON_CORE
    abbreviated_title = factory.fuzzy.FuzzyText(length=20, chars=string.ascii_uppercase)
    titles = factory.LazyAttribute(generate_titles)
    credits = factory.fuzzy.FuzzyInteger(60, 180)
    content_constraint = factory.LazyAttribute(generate_content_constraint)
    management_entity = factory.LazyAttribute(generate_management_entity)
    teaching_campus = factory.LazyAttribute(generate_teaching_campus)
    remark = factory.LazyAttribute(generate_remark)
    start_year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)
    end_year = None
