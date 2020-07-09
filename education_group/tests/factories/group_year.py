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
import random
import string

import factory.fuzzy

from base.models.enums import active_status
from base.models.learning_unit_year import MAXIMUM_CREDITS, MINIMUM_CREDITS
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from education_group.models.enums.constraint_type import CREDITS
from education_group.tests.factories.group import GroupFactory


def string_generator(nb_char=8):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(nb_char))


def generate_title(group_year):
    if group_year.acronym:
        return '{obj.group.start_year} {obj.acronym}'.format(obj=group_year).lower()
    return '{obj.group.start_year} {gen_str}'.format(obj=group_year, gen_str=string_generator()).lower()


class GroupYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "education_group.GroupYear"

    partial_acronym = factory.Sequence(lambda n: 'PGy %d' % n)
    acronym = factory.Sequence(lambda n: 'Gy %d' % n)
    education_group_type = factory.SubFactory(EducationGroupTypeFactory)
    credits = factory.fuzzy.FuzzyInteger(MINIMUM_CREDITS, MAXIMUM_CREDITS)
    constraint_type = CREDITS
    min_constraint = factory.fuzzy.FuzzyInteger(1, MAXIMUM_CREDITS)
    max_constraint = factory.lazy_attribute(lambda a: a.min_constraint)
    group = factory.SubFactory(GroupFactory)
    title_fr = factory.LazyAttribute(generate_title)
    title_en = factory.LazyAttribute(generate_title)
    remark_fr = factory.fuzzy.FuzzyText(length=255)
    remark_en = factory.fuzzy.FuzzyText(length=255)
    academic_year = factory.SubFactory(AcademicYearFactory, year=factory.SelfAttribute("..group.start_year.year"))
    active = active_status.ACTIVE
    main_teaching_campus = factory.SubFactory(CampusFactory)
