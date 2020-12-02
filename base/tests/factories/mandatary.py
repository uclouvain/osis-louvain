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
from factory.django import DjangoModelFactory
from faker import Faker

from base.tests.factories.mandate import MandateFactory
from base.tests.factories.person import PersonFactory

fake = Faker()


def generate_start_date(academic_calendar):
    if academic_calendar.academic_year:
        return academic_calendar.academic_year.start_date
    else:
        return datetime.date(datetime.timezone.now().year, 9, 30)


def generate_end_date(academic_calendar):
    if academic_calendar.academic_year:
        return academic_calendar.academic_year.end_date
    else:
        return datetime.date(datetime.timezone.now().year + 1, 9, 30)


class MandataryFactory(DjangoModelFactory):
    class Meta:
        model = "base.Mandatary"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1),
                                          datetime.datetime(2017, 3, 1))
    mandate = factory.SubFactory(MandateFactory)
    person = factory.SubFactory(PersonFactory)
    start_date = factory.LazyAttribute(generate_start_date)
    end_date = factory.LazyAttribute(generate_end_date)
