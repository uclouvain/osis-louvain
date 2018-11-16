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
import datetime

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from base.tests.factories.academic_calendar import AcademicCalendarFactory

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.forms.academic_calendar import AcademicCalendarForm
from django.test.utils import override_settings


class TestAcademicCalendarForm(TestCase):
    def setUp(self):
        self.an_academic_year = AcademicYearFactory()

    def test_with_start_and_end_dates_not_set(self):
        form = AcademicCalendarForm(data={
            "academic_year": self.an_academic_year.pk,
            "title": "Academic event",
            "description": "Description of an academic event"
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['start_date'], _('Start date and end date are mandatory'))

    def test_with_start_date_higher_than_end_date(self):
        form = AcademicCalendarForm(data={
            "academic_year": self.an_academic_year.pk,
            "title": "Academic event",
            "description": "Description of an academic event",
            "start_date": datetime.date.today(),
            "end_date": datetime.date.today() - datetime.timedelta(days=2)
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['start_date'], _('Start date must be lower than end date'))

    @override_settings(USE_TZ=False)
    def test_with_end_date_inferior_to_offer_year_calendar_end_date(self):
        an_academic_calendar = AcademicCalendarFactory(academic_year=self.an_academic_year)
        an_offer_year = OfferYearFactory(academic_year=self.an_academic_year)
        an_offer_year_calendar = OfferYearCalendarFactory(academic_calendar=an_academic_calendar,
                                                          offer_year=an_offer_year)

        form = AcademicCalendarForm(data={
            "academic_year": self.an_academic_year.pk,
            "title": "New title",
            "start_date": an_academic_calendar.start_date,
            "end_date": an_offer_year_calendar.end_date - datetime.timedelta(days=2)
        }, instance=an_academic_calendar)
        self.assertFalse(form.is_valid())
        date_format = str(_('date_format'))
        self.assertEqual(
            form.errors['end_date'],
            _("The closure's date of '%s' of the academic calendar can't be "
              "lower than %s (end date of '%s' of the program '%s')")
            % (an_academic_calendar.title,
               an_offer_year_calendar.end_date.strftime(date_format),
               an_academic_calendar.title,
               an_offer_year_calendar.offer_year.acronym)
        )

    def test_with_correct_form(self):
        form = AcademicCalendarForm(data={
            "academic_year": self.an_academic_year.pk,
            "title": "Academic event",
            "description": "Description of an academic event",
            "start_date": datetime.date.today(),
            "end_date": datetime.date.today() + datetime.timedelta(days=2)
        })
        self.assertTrue(form.is_valid())
