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
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from base.signals.publisher import compute_scores_encodings_deadlines
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory

YEAR_CALENDAR = timezone.now().year


class OfferYearCalendarsAttributesValidation(TestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory(year=YEAR_CALENDAR,
                                                 start_date=datetime.date(YEAR_CALENDAR, 9, 1),
                                                 end_date=datetime.date(YEAR_CALENDAR+1, 10, 30))
        self.academic_calendar = AcademicCalendarFactory(academic_year=self.academic_year,
                                                         start_date=datetime.date(YEAR_CALENDAR, 9, 1),
                                                         end_date=datetime.date(YEAR_CALENDAR+1, 10, 30))
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)

    def test_end_date_lower_than_start_date(self):
        self.offer_year_calendar = OfferYearCalendarFactory(offer_year=self.offer_year,
                                                            academic_calendar=self.academic_calendar)
        self.offer_year_calendar.start_date = datetime.date(YEAR_CALENDAR, 9, 1)
        self.offer_year_calendar.end_date = datetime.date(YEAR_CALENDAR, 8, 1)
        with self.assertRaises(ValidationError):
            self.offer_year_calendar.save()

    def test_compute_deadline_is_called_case_offer_year_calendar_save(self):
        with mock.patch.object(compute_scores_encodings_deadlines, 'send') as mock_method:
            OfferYearCalendarFactory()
            self.assertTrue(mock_method.called)

