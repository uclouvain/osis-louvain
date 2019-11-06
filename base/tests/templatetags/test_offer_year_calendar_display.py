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

from django.test import TestCase

from base.templatetags import offer_year_calendar_display as offer_year_calendar_display_tag
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory

today = datetime.date.today()
today2 = datetime.datetime.today()


class OfferYearCalendarDisplayTagTest(TestCase):

    def setUp(self):

        self.build_current_offer_yr_calendar()
        self.build_old_offer_yr_calendar()

    def build_old_offer_yr_calendar(self):
        self.previous_academic_year = AcademicYearFactory(start_date=today.replace(year=today.year - 3),
                                                          end_date=today.replace(year=today.year - 2),
                                                          year=today.year - 3)
        an_previous_academic_calendar = AcademicCalendarFactory(academic_year=self.previous_academic_year)
        self.a_previous_offer_year = OfferYearFactory(academic_year=self.previous_academic_year)
        self.a_previous_offer_yr_calendar = OfferYearCalendarFactory(academic_calendar=an_previous_academic_calendar,
                                                                     offer_year=self.a_previous_offer_year)

    def build_current_offer_yr_calendar(self):
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        an_academic_calendar = AcademicCalendarFactory(academic_year=self.current_academic_year)
        self.a_current_offer_year = OfferYearFactory(academic_year=self.current_academic_year)
        self.a_current_offer_yr_calendar = OfferYearCalendarFactory(academic_calendar=an_academic_calendar,
                                                               offer_year=self.a_current_offer_year)

    def test_current_offer_year_calendar_display_style(self):
        css_style = offer_year_calendar_display_tag\
            .offer_year_calendar_display(self.a_current_offer_yr_calendar.start_date,
                                         self.a_current_offer_yr_calendar.end_date)
        self.assertEqual(css_style, offer_year_calendar_display_tag.CURRENT_EVENT_CSS_STYLE)

    def test_not_current_offer_year_calendar_display_style(self):
        css_style = offer_year_calendar_display_tag\
            .offer_year_calendar_display(self.a_previous_offer_yr_calendar.start_date,
                                         self.a_previous_offer_yr_calendar.end_date)
        self.assertEqual(css_style, offer_year_calendar_display_tag.NOT_CURRENT_EVENT_CSS_STYLE)
