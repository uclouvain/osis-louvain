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
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils import formats
from django.utils.translation import gettext as _
from reversion.admin import VersionAdmin

from base.models.abstracts.abstract_calendar import AbstractCalendar
from base.signals.publisher import compute_scores_encodings_deadlines
from osis_common.models.osis_model_admin import OsisModelAdmin


class OfferYearCalendarAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('academic_calendar', 'education_group_year', 'start_date', 'end_date', 'changed',)
    search_fields = ['education_group_year__acronym']
    list_filter = ('academic_calendar__academic_year', 'academic_calendar__reference',)


class OfferYearCalendar(AbstractCalendar):
    education_group_year = models.ForeignKey('EducationGroupYear', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('academic_calendar', 'education_group_year')

    def clean(self):
        super().clean()

        self._check_is_in_calendar_range(self.start_date)
        self._check_is_in_calendar_range(self.end_date)

    def _check_is_in_calendar_range(self, date):
        if date and not self.academic_calendar.start_date <= date.date() <= self.academic_calendar.end_date:
            info = {
                "date": formats.localize_input(date.date()),
                "start_date": formats.localize_input(self.academic_calendar.start_date),
                "end_date": formats.localize_input(self.academic_calendar.end_date),
            }
            raise ValidationError(_('%(date)s must be set within %(start_date)s and %(end_date)s'), params=info)

    def save(self, *args, **kwargs):
        self.end_start_dates_validation()
        super(OfferYearCalendar, self).save(*args, **kwargs)
        compute_scores_encodings_deadlines.send(sender=self.__class__, offer_year_calendar=self)

    def _dates_are_set(self):
        return bool(self.start_date and self.end_date)

    def __str__(self):
        return u"%s - %s" % (self.academic_calendar, self.education_group_year)


def find_latest_end_date_by_academic_calendar(academic_calendar_id):
    try:
        return OfferYearCalendar.objects.filter(academic_calendar_id=academic_calendar_id) \
            .filter(end_date__isnull=False) \
            .latest('end_date')
    except ObjectDoesNotExist:
        return None


def find_by_education_group_year(education_group_year):
    return OfferYearCalendar.objects.filter(education_group_year=education_group_year)


def search(**kwargs):

    queryset = OfferYearCalendar.objects

    if 'education_group_year_id' in kwargs:
        queryset = queryset.filter(education_group_year=kwargs['education_group_year_id'])

    if 'academic_calendar_reference' in kwargs:
        queryset = queryset.filter(academic_calendar__reference=kwargs['academic_calendar_reference'])

    if 'number_session' in kwargs:
        queryset = queryset.filter(academic_calendar__sessionexamcalendar__number_session=kwargs['number_session'])

    return queryset


def create_offer_year_calendar(education_group_yr, academic_calendar):
    return OfferYearCalendar(education_group_year=education_group_yr,
                             academic_calendar=academic_calendar)
