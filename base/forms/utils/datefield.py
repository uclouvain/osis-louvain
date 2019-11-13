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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import formats
from django.utils.translation import gettext_lazy as _

DATE_FORMAT = '%d/%m/%Y'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = DATE_FORMAT + ' ' + TIME_FORMAT
DATE_RANGE_SPLITTER = ' - '
DATE_RANGE_FORMAT = DATE_FORMAT + DATE_RANGE_SPLITTER + DATE_FORMAT

# Format for the widgets in javascript
DATE_FORMAT_JS = 'DD/MM/YYYY'
TIME_FORMAT_JS = 'HH:mm'
DATETIME_FORMAT_JS = DATE_FORMAT_JS + ' ' + TIME_FORMAT_JS


def _add_min_max_value(widget, min_date, max_date):
    if isinstance(min_date, datetime.date):
        min_date = formats.localize_input(min_date, widget.format)
    widget.attrs['data-minDate'] = min_date

    if isinstance(max_date, datetime.date):
        max_date = formats.localize_input(max_date, widget.format)
    widget.attrs['data-maxDate'] = max_date


class DatePickerInput(forms.DateInput):

    defaut_attrs = {
                'class': 'datepicker',
                'data-format': DATE_FORMAT_JS
            }

    def __init__(self, attrs=None, format=DATE_FORMAT):
        super().__init__(attrs=attrs or self.defaut_attrs)
        self.format = format

    def add_min_max_value(self, min_date, max_date):
        _add_min_max_value(self, min_date, max_date)


class DateTimePickerInput(forms.MultiWidget):
    def __init__(self):
        widgets = (
            DatePickerInput(
                format=DATE_FORMAT,
            ),
            forms.TimeInput(
                attrs={
                    'data-format': TIME_FORMAT_JS,
                    'type': 'time'
                },
                format=TIME_FORMAT,
            ),
        )

        super().__init__(widgets)

    def add_min_max_value(self, min_date, max_date):
        self.widgets[0].add_min_max_value(min_date, max_date)

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]


class DateRangePickerInput(forms.TextInput):

    default_attrs = {
                'class': 'daterange',
                'data-format': DATE_FORMAT_JS
            }

    def __init__(self, attrs=None, format=DATE_FORMAT):
        super().__init__(attrs=attrs or self.default_attrs)
        self.format = format

    def format_value(self, value):
        if isinstance(value, tuple) and len(value) == 2:
            if all(isinstance(i, datetime.date) for i in value):
                return self.__format_date(value[0]) + DATE_RANGE_SPLITTER + self.__format_date(value[1])
            else:
                return ''
        else:
            return value

    def __format_date(self, value):
        return formats.localize_input(value, self.format)

    def add_min_max_value(self, min_date, max_date):
        _add_min_max_value(self, min_date, max_date)


class DateRangeField(forms.DateField):
    input_formats = DATE_RANGE_FORMAT
    widget = DateRangePickerInput

    def __init__(self, base=forms.DateField(), input_formats=None, **kwargs):
        """
        :param base: can be either DateField or DateTimeField, which will be used
        to do conversions for beginning and end of interval.
        :param input_formats: is passed into base if present
        """
        super(DateRangeField, self).__init__(**kwargs)
        self.base = base
        if input_formats is not None:
            self.base.input_formats = input_formats
        else:
            self.base.input_formats = [DATE_FORMAT]

    def to_python(self, value):
        if self.required is False and not value:
            return None

        values = value.split(DATE_RANGE_SPLITTER)
        if len(values) != 2:
            raise ValidationError(_('The format of the range date is not valid'))
        start_date = self.base.to_python(values[0])
        end_date = self.base.to_python(values[1])
        if start_date > end_date:
            raise ValidationError(_('The start date must be equals or lower than the end date'))
        return start_date, end_date
