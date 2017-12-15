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
from django.utils import timezone

from django.forms import formset_factory

from base.forms.education_groups_administrative_data import AdministrativeDataSession, AdministrativeData, \
    DATETIME_FORMAT, DATE_FORMAT, AdministrativeDataFormset
from base.models.enums import academic_calendar_type
from base.models.offer_year_calendar import OfferYearCalendar
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory

from django.test import TestCase


class TestAdministrativeDataForm(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(year=2007)

        self.academic_calendars = [
            AcademicCalendarFactory.build(reference=i[0],
                                          academic_year=self.academic_year)
            for i in academic_calendar_type.ACADEMIC_CALENDAR_TYPES
        ]

        for ac in self.academic_calendars:
            ac.save(functions=[])

        self.education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)

        self.offer_year = [
            OfferYearCalendarFactory(education_group_year=self.education_group_year,
                                     academic_calendar=i)
            for i in self.academic_calendars
        ]

        self.session_exam_calendars = []
        for ac in self.academic_calendars:
            self.session_exam_calendars.extend(
                [
                    SessionExamCalendarFactory(number_session=i, academic_calendar=ac)
                    for i in range(1, 4)
                ]
            )

    def test_initial(self):
        formset_session = AdministrativeDataFormset(form_kwargs={'education_group_year': self.education_group_year})

        for form in formset_session:
            for field in form.fields.values():
                self.assertIsNotNone(field.initial)
                self.assertIsNotNone(field.widget.attrs.get("data-maxDate"))
                self.assertIsNotNone(field.widget.attrs.get("data-minDate"))

    def test_save(self):
        deliberation_date = '08/12/{} 10:50'.format(self.academic_year.year)
        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year+1)
        exam_submission = '14/12/{}'.format(self.academic_year.year)
        form_data = {
            'form-0-deliberation': deliberation_date,
            'form-0-dissertation_submission': '',
            'form-0-exam_enrollment_range': exam_enrollment_start + ' - ' + exam_enrollment_end,
            'form-0-scores_exam_diffusion': '',
            'form-0-scores_exam_submission': exam_submission,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }

        SessionFormSet = formset_factory(form=AdministrativeDataSession, formset=AdministrativeData, extra=1)
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': self.education_group_year})

        self.assertEqual(formset_session.errors, [{}])
        self.assertTrue(formset_session.is_valid())
        formset_session.save()

        oyc = formset_session.forms[0]._get_offer_year_calendar('exam_enrollment_range')
        self.assertEqual(exam_enrollment_start, timezone.localtime(oyc.start_date).strftime(DATE_FORMAT))
        self.assertEqual(exam_enrollment_end, timezone.localtime(oyc.end_date).strftime(DATE_FORMAT))

        oyc = formset_session.forms[0]._get_offer_year_calendar('deliberation')
        self.assertEqual(deliberation_date, timezone.localtime(oyc.start_date).strftime(DATETIME_FORMAT))

    def test_save_errors(self):
        deliberation_date = '08/12/1900 10:50'
        exam_enrollment_start = '20/12/2015'
        exam_enrollment_end = '15/01/2018'
        form_data = {
            'form-0-deliberation': deliberation_date,
            'form-0-dissertation_submission': '',
            'form-0-exam_enrollment_range': exam_enrollment_start + ' - ' + exam_enrollment_end,
            'form-0-scores_exam_diffusion': '',
            'form-0-scores_exam_submission': '14/12/1900',
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }

        SessionFormSet = formset_factory(form=AdministrativeDataSession, formset=AdministrativeData, extra=1)
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': self.education_group_year})

        self.assertFalse(formset_session.is_valid())
        self.assertEqual(len(formset_session.errors[0]), 3)

    def test_get_form_kwargs(self):
        formset = AdministrativeData(form_kwargs={'education_group_year': self.education_group_year})

        result = formset.get_form_kwargs(0)
        self.assertEqual(result.get('session'), 1)
        self.assertEqual(result.get('education_group_year'), self.education_group_year)

        from base.models import session_exam_calendar
        session = session_exam_calendar.find_by_session_and_academic_year(1, self.education_group_year.academic_year)
        acs = [s.academic_calendar for s in session]
        self.assertEqual(list(result.get('list_offer_year_calendar')),
                         list(OfferYearCalendar.objects.filter(education_group_year=self.education_group_year,
                                                               academic_calendar__in=acs)))
