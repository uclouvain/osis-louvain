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

from django.forms import formset_factory, MultiWidget
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import gettext_lazy as _

from base.forms.education_groups_administrative_data import AdministrativeDataSessionForm, AdministrativeDataFormSet, \
    DATE_FORMAT, _build_new_course_enrollment_offer_yr_calendar, CourseEnrollmentForm, AdditionalInfoForm
from base.forms.utils.datefield import DATETIME_FORMAT
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.enums import academic_calendar_type
from base.models.offer_year_calendar import OfferYearCalendar
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory


class TestAdministrativeDataForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2007)

        cls.academic_calendars = [
            AcademicCalendarFactory(reference=i[0], academic_year=cls.academic_year)
            for i in academic_calendar_type.CALENDAR_TYPES
        ]

        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)

        cls.offer_year = [
            OfferYearCalendarFactory(education_group_year=cls.education_group_year, academic_calendar=ac)
            for ac in cls.academic_calendars
        ]

        cls.session_exam_calendars = [
            SessionExamCalendarFactory(number_session=1, academic_calendar=ac) for ac in cls.academic_calendars
        ]

    def test_initial(self):
        SessionFormSet = formset_factory(form=AdministrativeDataSessionForm, formset=AdministrativeDataFormSet)
        formset_session = SessionFormSet(form_kwargs={'education_group_year': self.education_group_year})
        for form in formset_session:
            for field in form.fields.values():
                self.assertIsNotNone(field.initial)
                if isinstance(field.widget, MultiWidget):
                    self.assertIsNotNone(field.widget.widgets[0].attrs.get("data-maxDate"))
                    self.assertIsNotNone(field.widget.widgets[0].attrs.get("data-minDate"))
                else:
                    self.assertIsNotNone(field.widget.attrs.get("data-maxDate"))
                    self.assertIsNotNone(field.widget.attrs.get("data-minDate"))

    def test_save(self):
        deliberation_date = '08/12/{}'.format(self.academic_year.year)
        deliberation_time = '10:50'
        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year+1)
        exam_submission = '14/12/{}'.format(self.academic_year.year)
        form_data = {
            'form-0-deliberation_0': deliberation_date,
            'form-0-deliberation_1': deliberation_time,
            'form-0-dissertation_submission': '',
            'form-0-exam_enrollment_range': exam_enrollment_start + ' - ' + exam_enrollment_end,
            'form-0-scores_exam_diffusion': '',
            'form-0-scores_exam_submission': exam_submission,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }

        SessionFormSet = formset_factory(form=AdministrativeDataSessionForm, formset=AdministrativeDataFormSet)
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': self.education_group_year})

        self.assertEqual(formset_session.errors, [{}])
        self.assertTrue(formset_session.is_valid())
        formset_session.save()

        oyc = formset_session.forms[0]._get_offer_year_calendar('exam_enrollment_range')
        self.assertEqual(exam_enrollment_start, oyc.start_date.strftime(DATE_FORMAT))
        self.assertEqual(exam_enrollment_end, oyc.end_date.strftime(DATE_FORMAT))

        oyc = formset_session.forms[0]._get_offer_year_calendar('deliberation')
        self.assertEqual(deliberation_date + ' ' + deliberation_time, oyc.start_date.strftime(DATETIME_FORMAT))

    def test_save_errors(self):
        deliberation_date = '08/12/1900'
        deliberation_time = '10:50'
        exam_enrollment_start = '20/12/2015'
        exam_enrollment_end = '15/01/2018'
        form_data = {
            'form-0-deliberation_0': deliberation_date,
            'form-0-deliberation_1': deliberation_time,
            'form-0-dissertation_submission': '',
            'form-0-exam_enrollment_range': exam_enrollment_start + ' - ' + exam_enrollment_end,
            'form-0-scores_exam_diffusion': '',
            'form-0-scores_exam_submission': '14/12/1900',
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }

        SessionFormSet = formset_factory(form=AdministrativeDataSessionForm, formset=AdministrativeDataFormSet)
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': self.education_group_year})

        self.assertFalse(formset_session.is_valid())
        self.assertEqual(len(formset_session.errors[0]), 3)

    def test_get_form_kwargs(self):
        formset = AdministrativeDataFormSet(form_kwargs={'education_group_year': self.education_group_year})

        result = formset.get_form_kwargs(0)
        self.assertEqual(result.get('session'), 1)
        self.assertEqual(result.get('education_group_year'), self.education_group_year)

        from base.models import session_exam_calendar
        session = session_exam_calendar.find_by_session_and_academic_year(1, self.education_group_year.academic_year)
        acs = [s.academic_calendar for s in session]
        self.assertEqual(list(result.get('list_offer_year_calendar')),
                         list(OfferYearCalendar.objects.filter(education_group_year=self.education_group_year,
                                                               academic_calendar__in=acs)))

    def test_dont_save_while_new_and_no_date(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)

        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year+1)

        form_data = {
            'form-0-exam_enrollment_range': exam_enrollment_start + ' - ' + exam_enrollment_end,
            'form-0-scores_exam_diffusion': '',
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }

        SessionFormSet = formset_factory(form=AdministrativeDataSessionForm, formset=AdministrativeDataFormSet)
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': education_group_yr})

        self.assertEqual(formset_session.errors, [{}])
        self.assertTrue(formset_session.is_valid())
        oyc = formset_session.forms[0]._get_offer_year_calendar('exam_enrollment_range')
        self.assertIsNone(oyc.id)
        oyc = formset_session.forms[0]._get_offer_year_calendar('scores_exam_diffusion')
        self.assertIsNone(oyc.id)

        formset_session.save()

        self.assertEqual(len(self._search_offer_year_calendar(education_group_yr,
                                                              academic_calendar_type.EXAM_ENROLLMENTS)),
                         1)
        self.assertEqual(len(self._search_offer_year_calendar(education_group_yr,
                                                              academic_calendar_type.SCORES_EXAM_DIFFUSION)),
                         0)

    def test_get_new_offer_year_calendar(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)
        SessionFormSet = formset_factory(form=AdministrativeDataSessionForm, formset=AdministrativeDataFormSet)

        form_data = {
            'form-0-exam_enrollment_range': '20/12/{}'.format(self.academic_year.year) + ' - ' + '15/01/{}'.format(
                self.academic_year.year + 1),
            'form-0-scores_exam_diffusion': '',
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }
        formset_session = SessionFormSet(data=form_data,
                                         form_kwargs={'education_group_year': education_group_yr})
        oyc = formset_session.forms[0]._get_offer_year_calendar('scores_exam_diffusion')
        self.assertIsNone(oyc.id)
        self.assertEqual(oyc.education_group_year, education_group_yr)
        self.assertIsNone(oyc.offer_year)

    def _search_offer_year_calendar(self, education_group_yr, a_reference):
        academic_calendar = AcademicCalendar.objects.get(sessionexamcalendar__number_session=1,
                                                         academic_year=education_group_yr.academic_year,
                                                         reference=a_reference)
        return OfferYearCalendar.objects.filter(education_group_year=education_group_yr,
                                                academic_calendar=academic_calendar)


class TestCourseEnrollmentForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2007)

    def test_get_new_course_enrollment_calendar(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)
        self.assertIsNone(_build_new_course_enrollment_offer_yr_calendar(education_group_yr))

        academic_cal_course_enrollment = AcademicCalendarFactory(reference=academic_calendar_type.COURSE_ENROLLMENT,
                                                                 academic_year=self.academic_year)
        new_oyc = _build_new_course_enrollment_offer_yr_calendar(education_group_yr)

        self.assertEqual(new_oyc.academic_calendar, academic_cal_course_enrollment)
        self.assertEqual(new_oyc.education_group_year, education_group_yr)
        self.assertIsNone(new_oyc.id)

    def test_clean(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)
        academic_cal_course_enrollment = AcademicCalendarFactory(reference=academic_calendar_type.COURSE_ENROLLMENT,
                                                                 academic_year=self.academic_year)

        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year+1)

        form = CourseEnrollmentForm(data={"range_date": exam_enrollment_start + ' - ' + exam_enrollment_end},
                                    instance=None, education_group_yr=education_group_yr)
        form.is_valid()
        self.assertEqual(form.instance.education_group_year, education_group_yr)
        self.assertEqual(form.instance.academic_calendar, academic_cal_course_enrollment)

    @override_settings(LANGUAGES=[('fr-be', 'Français'), ], LANGUAGE_CODE='fr-be')
    def test_clean_with_validation_error(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)
        AcademicCalendarFactory(reference=academic_calendar_type.COURSE_ENROLLMENT,
                                academic_year=self.academic_year)

        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year-2)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year-1)

        form = CourseEnrollmentForm(data={"range_date": exam_enrollment_start + ' - ' + exam_enrollment_end},
                                    instance=None, education_group_yr=education_group_yr)
        form.is_valid()

        self.assertEqual(form.errors["range_date"][0],
                         "{} doit être comprise entre {} et {}"
                         .format(exam_enrollment_start,
                                 self.academic_year.start_date.strftime(DATE_FORMAT),
                                 self.academic_year.end_date.strftime(DATE_FORMAT)))

    @override_settings(LANGUAGES=[('fr-be', 'Français'), ], LANGUAGE_CODE='fr-be')
    def test_clean_with_validation_error_in_date(self):
        education_group_yr = EducationGroupYearFactory(academic_year=self.academic_year)
        AcademicCalendarFactory(reference=academic_calendar_type.COURSE_ENROLLMENT,
                                academic_year=self.academic_year)

        exam_enrollment_start = '20/12/{}'.format(self.academic_year.year)
        exam_enrollment_end = '15/01/{}'.format(self.academic_year.year)

        form = CourseEnrollmentForm(data={"range_date": exam_enrollment_start + ' - ' + exam_enrollment_end},
                                    instance=None, education_group_yr=education_group_yr)
        form.is_valid()
        self.assertEqual(form.errors["range_date"][0],
                         _('The start date must be equals or lower than the end date'))


class TestAdditionalInfoForm(TestCase):
    def test_get_new_course_enrollment_calendar(self):
        academic_year = AcademicYearFactory(year=2017)
        education_group_yr = EducationGroupYearFactory(
            academic_year=academic_year,
            weighting=True,
            default_learning_unit_enrollment=False,
        )
        form = AdditionalInfoForm(
            {
                "weighting": False,
                "default_learning_unit_enrollment": True,
            },
            instance=education_group_yr)
        form.save()
        updated_education_group_yr = EducationGroupYear.objects.get(pk=education_group_yr.pk)
        self.assertFalse(updated_education_group_yr.weighting)
        self.assertTrue(updated_education_group_yr.default_learning_unit_enrollment)
