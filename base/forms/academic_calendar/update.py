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
from django import forms
from django.core.exceptions import ValidationError

from base.forms.utils.datefield import DatePickerInput
from django.utils.translation import gettext_lazy as _


class AcademicCalendarUpdateForm(forms.Form):
    start_date = forms.DateField(label=_("Start date"), widget=DatePickerInput())
    end_date = forms.DateField(widget=DatePickerInput(), label=_("End date"), required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if all([cleaned_data.get('end_date'), cleaned_data.get('start_date')]) \
                and cleaned_data['end_date'] < cleaned_data['start_date']:
            raise ValidationError({
                'end_date': _("%(max)s must be greater or equals than %(min)s") % {
                    "max": _("End date"),
                    "min": _("Start date"),
                }
            })
        return cleaned_data
