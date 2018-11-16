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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from operator import itemgetter

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.translation import ugettext_lazy as _

from base.forms import bootstrap
from base.models import offer_year_calendar, academic_year
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums import academic_calendar_type


def _get_sorted_choices(li):
    return sorted(((a, _(b)) for (a, b) in li), key=itemgetter(1))


class AcademicCalendarForm(bootstrap.BootstrapModelForm):
    REFERENCE_CHOICE_FIELD = (
        BLANK_CHOICE_DASH[0],
        (
            _("academic events").capitalize(),
            _get_sorted_choices(academic_calendar_type.ACADEMIC_CALENDAR_TYPES)
        ),
        (
            _("project events").capitalize(),
            _get_sorted_choices(academic_calendar_type.PROJECT_CALENDAR_TYPES)
        ),
        (
            _("ad hoc events").capitalize(),
            _get_sorted_choices(academic_calendar_type.AD_HOC_CALENDAR_TYPES),
        ),
    )

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all().order_by('year'),
        widget=forms.Select(),
        empty_label=None,
    )
    reference = forms.ChoiceField(choices=REFERENCE_CHOICE_FIELD, required=False)

    class Meta:
        model = AcademicCalendar
        exclude = ['external_id', 'changed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].initial = academic_year.starting_academic_year()

    def save(self, commit=True):
        instance = super(AcademicCalendarForm, self).save(commit=False)
        if commit:
            instance.save()
        return instance

    def end_date_gt_last_offer_year_calendar_end_date(self):
        off_year_calendar_max = offer_year_calendar.find_latest_end_date_by_academic_calendar(self.instance.id)
        date_format = str(_('date_format'))
        if off_year_calendar_max and self.cleaned_data['end_date'] and off_year_calendar_max.end_date \
                and self.cleaned_data['end_date'] < off_year_calendar_max.end_date.date():
            self._errors['end_date'] = _("The closure's date of '%s' of the academic calendar can't be "
                                         "lower than %s (end date of '%s' of the program '%s')") % (
                                           self.instance.title,
                                           off_year_calendar_max.end_date.date().strftime(date_format),
                                           self.instance.title,
                                           off_year_calendar_max.offer_year.acronym
                                       )
            return False
        return True

    def end_date_gt_start_date(self):
        if self.cleaned_data['end_date'] <= self.cleaned_data['start_date']:
            self._errors['start_date'] = _('Start date must be lower than end date')
            return False
        return True

    def is_valid(self):
        return super(AcademicCalendarForm, self).is_valid() \
               and self.start_date_and_end_date_are_set() \
               and self.end_date_gt_last_offer_year_calendar_end_date() \
               and self.end_date_gt_start_date()

    def start_date_and_end_date_are_set(self):
        if not self.cleaned_data.get('end_date') or not self.cleaned_data.get('start_date'):
            error_msg = "{0}".format(_('Start date and end date are mandatory'))
            self._errors['start_date'] = error_msg
            return False
        return True
