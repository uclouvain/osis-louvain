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

import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory

from base.models.academic_year import AcademicYear


def create_current_academic_year():
    return AcademicYearFactory(year=get_current_year())


def get_current_year():
    now = datetime.datetime.now()
    ref_date = datetime.datetime(now.year, 9, 15)
    if now < ref_date:
        start_date = datetime.date(now.year - 1, 9, 15)
    else:
        start_date = datetime.date(now.year, 9, 15)
    return start_date.year


class AcademicYearFactory(DjangoModelFactory):
    class Meta:
        model = "base.AcademicYear"
        django_get_or_create = ('year',)

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1),
                                               datetime.datetime(2017, 3, 1))
    year = factory.fuzzy.FuzzyInteger(1950, timezone.now().year)
    start_date = factory.LazyAttribute(lambda obj: datetime.date(obj.year, 9, 15))
    end_date = factory.LazyAttribute(lambda obj: datetime.date(obj.year + 1, 9, 30))

    class Params:
        current = factory.Trait(
            year=get_current_year()
        )

    @staticmethod
    def produce_in_past(from_year=None, quantity=3):
        from_year = from_year or get_current_year()
        return [AcademicYearFactory(year=from_year-i) for i in range(quantity)]

    @staticmethod
    def produce_in_future(current_year=None, quantity=10):
        current_year = current_year or get_current_year()
        academic_years = [AcademicYearFactory.build(year=current_year + i) for i in range(quantity)]
        return AcademicYear.objects.bulk_create(academic_years)

    @staticmethod
    def produce(base_year=None, number_past=1, number_future=1):
        current_year = base_year or get_current_year()
        acys = [AcademicYearFactory.build(year=current_year+i) for i in range(-number_past, number_future+1)]
        return AcademicYear.objects.bulk_create(acys)
