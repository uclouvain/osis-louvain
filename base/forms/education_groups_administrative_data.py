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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import formset_factory

from base.forms.bootstrap import BootstrapForm
from base.forms.utils.datefield import DateRangeField, DatePickerInput, DATE_FORMAT, DateTimePickerInput, \
    DATETIME_FORMAT, _convert_date_to_datetime, _convert_datetime_to_date
from base.models import offer_year_calendar, session_exam_calendar
from base.models.enums import academic_calendar_type
from django.utils.translation import ugettext_lazy as _


NUMBER_SESSIONS = 3


class CourseEnrollmentForm(BootstrapForm):
    range_date = DateRangeField(required=False, label=_("course_enrollment"))

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['range_date'].initial = (
                _convert_datetime_to_date(self.instance.start_date),
                _convert_datetime_to_date(self.instance.end_date))
            self.fields['range_date'].widget.add_min_max_value(self.instance.academic_calendar.start_date,
                                                               self.instance.academic_calendar.end_date)

    def clean_range_date(self):
        range_date = self.cleaned_data["range_date"]
        _set_values_in_offer_year_calendar(self.instance, range_date)
        return range_date

    def clean(self):
        try:
            self.instance.clean()
        except ValidationError as e:
            self.add_error('range_date', e)

    def save(self):
        self.instance.save()


class AdministrativeDataSession(BootstrapForm):
    exam_enrollment_range = DateRangeField(label=_('EXAM_ENROLLMENTS'), required=False)

    scores_exam_submission = forms.DateField(widget=DatePickerInput(format=DATE_FORMAT),
                                             input_formats=[DATE_FORMAT, ],
                                             label=_('marks_presentation'),
                                             required=False)

    dissertation_submission = forms.DateField(widget=DatePickerInput(format=DATE_FORMAT),
                                              input_formats=[DATE_FORMAT, ],
                                              label=_('dissertation_presentation'),
                                              required=False)

    deliberation = forms.DateTimeField(widget=DateTimePickerInput(format=DATETIME_FORMAT),
                                       input_formats=[DATETIME_FORMAT, ],
                                       label=_('DELIBERATION'), required=False)

    scores_exam_diffusion = forms.DateTimeField(widget=DateTimePickerInput(format=DATETIME_FORMAT),
                                                input_formats=[DATETIME_FORMAT, ],
                                                label=_("scores_diffusion"),
                                                required=False)

    def __init__(self, *args, **kwargs):
        self.education_group_year = kwargs.pop('education_group_year')
        self.session = kwargs.pop('session')
        self.list_offer_year_calendar = kwargs.pop('list_offer_year_calendar')
        super().__init__(*args, **kwargs)

        if self.list_offer_year_calendar:
            self._init_fields()
        else:
            raise ObjectDoesNotExist('There is no OfferYearCalendar for the education_group_year {}'
                                     .format(self.education_group_year))

    def _get_academic_calendar_type(self, name):
        if name == 'exam_enrollment_range':
            ac_type = academic_calendar_type.EXAM_ENROLLMENTS
        elif name == 'scores_exam_submission':
            ac_type = academic_calendar_type.SCORES_EXAM_SUBMISSION
        elif name == 'dissertation_submission':
            ac_type = academic_calendar_type.DISSERTATION_SUBMISSION
        elif name == 'deliberation':
            ac_type = academic_calendar_type.DELIBERATION
        elif name == 'scores_exam_diffusion':
            ac_type = academic_calendar_type.SCORES_EXAM_DIFFUSION
        else:
            ac_type = None

        return ac_type

    def _get_offer_year_calendar(self, field_name):
        ac_type = self._get_academic_calendar_type(field_name)
        oyc = self.list_offer_year_calendar.filter(academic_calendar__reference=ac_type).first()
        if not oyc:
            raise ObjectDoesNotExist('There is no OfferYearCalendar for the reference {}'
                                     .format(ac_type))
        return oyc

    def _init_fields(self):
        for name, field in self.fields.items():
            oyc = self._get_offer_year_calendar(name)
            if not oyc:
                continue

            if isinstance(field, DateRangeField):
                field.initial = (_convert_datetime_to_date(oyc.start_date),
                                 _convert_datetime_to_date(oyc.end_date))
            elif isinstance(field, forms.DateField):
                field.initial = _convert_datetime_to_date(oyc.start_date)
            else:
                field.initial = oyc.start_date

            field.widget.add_min_max_value(oyc.academic_calendar.start_date, oyc.academic_calendar.end_date)

    def save(self):
        for name, value in self.cleaned_data.items():
            oyc = self._get_offer_year_calendar(name)
            _set_values_in_offer_year_calendar(oyc, value)

            oyc.save()

    def clean(self):
        for name, value in list(self.cleaned_data.items()):
            oyc = self._get_offer_year_calendar(name)
            _set_values_in_offer_year_calendar(oyc, value)

            try:
                oyc.clean()
            except ValidationError as e:
                self.add_error(name, e)


def _set_values_in_offer_year_calendar(oyc, value):
    if isinstance(value, tuple) and len(value) == 2:
        oyc.start_date = _convert_date_to_datetime(value[0])
        oyc.end_date = _convert_date_to_datetime(value[1])
    else:
        oyc.start_date = _convert_date_to_datetime(value)
        oyc.end_date = _convert_date_to_datetime(value)


class AdministrativeData(forms.BaseFormSet):

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['session'] = index + 1

        education_group_year = kwargs.get('education_group_year')
        if not education_group_year:
            return kwargs

        q = offer_year_calendar.find_by_education_group_year(education_group_year)
        sessions = session_exam_calendar.find_by_session_and_academic_year(index + 1,
                                                                           education_group_year.academic_year)
        academic_calendar_list = [s.academic_calendar for s in sessions]
        kwargs['list_offer_year_calendar'] = q.filter(academic_calendar__in=academic_calendar_list) \
            if academic_calendar_list else None

        return kwargs

    def save(self):
        for form in self.forms:
            form.save()


AdministrativeDataFormset = formset_factory(form=AdministrativeDataSession,
                                            formset=AdministrativeData,
                                            extra=NUMBER_SESSIONS)
