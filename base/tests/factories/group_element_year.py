##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
import string
import random

import factory.fuzzy

from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.utils.fuzzy import FuzzyBoolean


def _generate_block_value():
    """Generate a random string composed of digit between 1 and 6 included.
    Each digit can be represented at most once in the string and they are sorted from smallest to greatest.

    Ex: "", "156", "2", "456" and so on
    """

    population = list(range(1, 7))
    k = random.randint(0, len(population))

    sample = random.sample(population, k)
    sample.sort()

    return int("".join([str(element) for element in sample])) if sample else None


class GroupElementYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.GroupElementYear"
        django_get_or_create = ('parent', 'child_branch', 'child_leaf')

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1), datetime.datetime(2017, 3, 1))
    parent = factory.SubFactory(EducationGroupYearFactory)
    child_branch = factory.SubFactory(EducationGroupYearFactory,
                                      academic_year=factory.SelfAttribute("..parent.academic_year"))
    relative_credits = factory.fuzzy.FuzzyInteger(0, 10)
    child_leaf = None
    is_mandatory = FuzzyBoolean()
    link_type = None
    order = None
    block = factory.LazyFunction(_generate_block_value)


class GroupElementYearChildLeafFactory(GroupElementYearFactory):
    child_branch = None
    child_leaf = factory.SubFactory(LearningUnitYearFactory,
                                    academic_year=factory.SelfAttribute("..parent.academic_year"))
