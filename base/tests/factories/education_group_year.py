##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import factory
import factory.fuzzy

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory


def generate_title(education_group_year):
    return '{obj.academic_year} {obj.acronym}'.format(obj=education_group_year).lower()


class EducationGroupYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.EducationGroupYear"

    education_group = factory.SubFactory(EducationGroupFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    acronym = factory.Sequence(lambda n: 'Education%d' % n)
    partial_acronym = factory.Sequence(lambda n: 'SCS%d' % n)
    title = factory.LazyAttribute(generate_title)
    title_english = factory.LazyAttribute(generate_title)
    education_group_type = factory.SubFactory(EducationGroupTypeFactory)
