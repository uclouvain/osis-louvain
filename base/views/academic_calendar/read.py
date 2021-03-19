##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
import datetime

from typing import Dict, List

from dal import autocomplete
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import django_filters
from django_filters.views import FilterView

from base.business.academic_calendar import AcademicEventRepository, AcademicSessionEvent
from base.forms.utils.datefield import DatePickerInput
from base.models import academic_year
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.utils.cache import CacheFilterMixin
from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_role.contrib.views import PermissionRequiredMixin


class AcademicCalendarFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(
        label=_("Start date"),
        widget=DatePickerInput(),
        required=True
    )
    to_date = django_filters.DateFilter(
        label=_("End date"),
        widget=DatePickerInput()
    )
    event_type = django_filters.MultipleChoiceFilter(
        label=_("Type"),
        choices=AcademicCalendarTypes.choices(),
        widget=autocomplete.Select2Multiple(url='academic_calendar_type_autocomplete',),
    )

    class Meta:
        model = AcademicCalendar
        fields = ('from_date', 'to_date', 'event_type', )

    @property
    def qs(self):
        academic_events = AcademicEventRepository().get_academic_events()
        if self.form.is_valid():
            academic_events = self._filter_academic_events(academic_events)
        return sorted(academic_events, key=lambda row: AcademicCalendarTypes.get_value(row.type))

    def _filter_academic_events(self, academic_events):
        if self.form.cleaned_data.get('from_date'):
            academic_events = filter(
                lambda event: event.end_date is None or event.end_date >= self.form.cleaned_data['from_date'],
                academic_events
            )
        if self.form.cleaned_data.get('to_date'):
            academic_events = filter(
                lambda event: event.start_date <= self.form.cleaned_data['to_date'],
                academic_events
            )
        if self.form.cleaned_data.get('event_type'):
            academic_events = filter(lambda event: event.type in self.form.cleaned_data['event_type'], academic_events)
        return academic_events


class AcademicCalendarsView(PermissionRequiredMixin, CacheFilterMixin, FilterView):
    indefinitely_date_value = '01-01-2099'
    permission_required = 'base.can_access_academic_calendar'
    raise_exception = True

    filterset_class = AcademicCalendarFilter
    template_name = "academic_calendar/academic_calendars.html"

    def get_filterset_kwargs(self, filterset_class):
        filterset_kwargs = super().get_filterset_kwargs(filterset_class)
        if filterset_kwargs['data'] is None:
            filterset_kwargs['data'] = self._get_default_filterset_data()
        return filterset_kwargs

    def _get_default_filterset_data(self) -> Dict:
        current_academic_year = academic_year.current_academic_year()
        return {
            'event_type': [
                AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
                AcademicCalendarTypes.EXAM_ENROLLMENTS.name,
                AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
                AcademicCalendarTypes.SCORES_EXAM_DIFFUSION.name,
                AcademicCalendarTypes.COURSE_ENROLLMENT.name,
                AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION.name,
                AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE.name,
                AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name,
                AcademicCalendarTypes.DELIBERATION.name,
                AcademicCalendarTypes.DISSERTATION_SUBMISSION.name,
            ],
            'from_date': current_academic_year.start_date if current_academic_year else datetime.date.today(),
            'to_date': current_academic_year.end_date if current_academic_year else None
        }

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'gantt_rows': self.get_gantt_rows()
        }

    def get_gantt_rows(self) -> List[Dict]:
        academic_events = self.object_list

        gantt_rows = []
        for type, events in itertools.groupby(academic_events, lambda row: row.type):
            gantt_rows.append({
                'id': type,
                'text': AcademicCalendarTypes.get_value(type),
                'type': 'project',
                'render': 'split',
                'color': 'transparent'
            })

            events = sorted(events, key=lambda row: row.start_date)
            gantt_rows += [{
                'text': self.__get_gantt_row_title_text(event),
                'tooltip_text': "{} ({})".format(event.title, display_as_academic_year(event.authorized_target_year)),
                'start_date': event.start_date.strftime('%d-%m-%Y'),
                'end_date': event.end_date.strftime('%d-%m-%Y') if event.end_date else self.indefinitely_date_value,
                'parent': type,
                'update_url': reverse('academic_calendar_update', kwargs={'academic_calendar_id': event.id})
            } for event in events]
        return gantt_rows

    def __get_gantt_row_title_text(self, event) -> str:
        text = display_as_academic_year(event.authorized_target_year)
        if (isinstance(event, AcademicSessionEvent)) and event.session is not None:
            text += ' (S{})'.format(str(event.session))
        return text
