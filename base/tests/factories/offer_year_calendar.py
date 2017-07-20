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

from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.offer_year import OfferYearFactory
from utils.helpers import get_tzinfo


def generate_start_date(offer_year_calendar):
    if offer_year_calendar.academic_calendar:
        return offer_year_calendar.academic_calendar.start_date
    else:
        return datetime.date(2000, 1, 1)

def generate_end_date(offer_year_calendar):
    if offer_year_calendar.academic_calendar:
        return offer_year_calendar.academic_calendar.end_date
    else:
        return datetime.date(2099, 1, 1)

class OfferYearCalendarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.OfferYearCalendar"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    academic_calendar = factory.SubFactory(AcademicCalendarFactory)
    offer_year = factory.SubFactory(OfferYearFactory)
    start_date = factory.LazyAttribute(generate_start_date)
    end_date = factory.LazyAttribute(generate_end_date)
    customized = False
