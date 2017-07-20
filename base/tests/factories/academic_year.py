##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

import factory
import factory.fuzzy
from django.conf import settings
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from utils.helpers import get_tzinfo

fake = Faker()


class AcademicYearFactory(DjangoModelFactory):
    class Meta:
        model = "base.AcademicYear"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    year = factory.fuzzy.FuzzyInteger(2000, timezone.now().year)
    start_date = factory.LazyAttribute(lambda obj: datetime.date(obj.year, 9, 15))
    end_date = factory.LazyAttribute(lambda obj: datetime.date(obj.year+1, 9, 30))


class AcademicYearFakerFactory(DjangoModelFactory):
    class Meta:
        model = "base.AcademicYear"
        django_get_or_create = ('year',)

    external_id = factory.Sequence(lambda n: '10000000%02d' % n)
    changed = fake.date_time_this_decade(before_now=True, after_now=True, tzinfo=get_tzinfo())
    start_date = fake.date_time_this_decade(before_now=True, after_now=False, tzinfo=get_tzinfo())
    end_date = fake.date_time_this_decade(before_now=False, after_now=True, tzinfo=get_tzinfo())
    year = factory.SelfAttribute('start_date.year')
