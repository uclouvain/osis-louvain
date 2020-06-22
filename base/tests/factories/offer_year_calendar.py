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

from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.offer_year import OfferYearFactory


def generate_start_date(abstract_calendar):
    if abstract_calendar.academic_calendar:
        return datetime.datetime(abstract_calendar.academic_calendar.start_date.year,
                                 abstract_calendar.academic_calendar.start_date.month,
                                 abstract_calendar.academic_calendar.start_date.day)
    else:
        return datetime.datetime(2000, 1, 1)


def generate_end_date(abstract_calendar):
    if abstract_calendar.academic_calendar:
        return datetime.datetime(abstract_calendar.academic_calendar.end_date.year,
                                 abstract_calendar.academic_calendar.end_date.month,
                                 abstract_calendar.academic_calendar.end_date.day)
    else:
        return datetime.datetime(2099, 1, 1)


class OfferYearCalendarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.OfferYearCalendar"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)

    academic_calendar = factory.SubFactory(AcademicCalendarFactory)
    offer_year = factory.SubFactory(OfferYearFactory)
    start_date = factory.LazyAttribute(generate_start_date)
    end_date = factory.LazyAttribute(generate_end_date)
    education_group_year = factory.SubFactory(EducationGroupYearFactory)
