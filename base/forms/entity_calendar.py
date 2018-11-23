##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.forms.utils.datefield import DatePickerInput, DATE_FORMAT
from base.models import entity_calendar
from base.models.academic_calendar import get_by_reference_and_academic_year
from base.models.academic_year import current_academic_year
from base.models.entity_calendar import EntityCalendar
from base.models.enums import academic_calendar_type


class EntityCalendarEducationalInformationForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=DatePickerInput(format=DATE_FORMAT),
        input_formats=[DATE_FORMAT, ],
        label=_("Educational information opening")
    )
    end_date = forms.DateTimeField(
        widget=DatePickerInput(format=DATE_FORMAT),
        input_formats=[DATE_FORMAT, ],
        label=_("Educational information ending")
    )

    class Meta:
        model = EntityCalendar
        fields = ["start_date", "end_date"]

    def __init__(self, entity_version, *args, **kwargs):
        entity_calendar_obj = entity_calendar.find_by_entity_and_reference(
            entity_version.entity.id, academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )
        initial = {} if entity_calendar_obj else find_summary_course_submission_dates_for_entity_version(entity_version)

        super().__init__(*args, instance=entity_calendar_obj, initial=initial, **kwargs)

    def save_entity_calendar(self, entity, *args, **kwargs):
        self.instance.entity = entity
        self.instance.academic_calendar = get_by_reference_and_academic_year(
            academic_calendar_type.SUMMARY_COURSE_SUBMISSION, current_academic_year())
        return self.save(*args, **kwargs)
