##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db import models
from django.utils import timezone
from django.contrib import admin
from base.models import offer_year


class OfferYearCalendarAdmin(admin.ModelAdmin):
    list_display = ('academic_calendar', 'offer_year', 'start_date', 'end_date', 'changed')
    fieldsets = ((None, {'fields': ('offer_year', 'academic_calendar', 'start_date', 'end_date')}),)
    raw_id_fields = ('offer_year',)
    search_fields = ['offer_year__acronym']
    list_filter = ('academic_calendar__title',)


class OfferYearCalendar(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    academic_calendar = models.ForeignKey('AcademicCalendar')
    offer_year = models.ForeignKey('OfferYear')
    start_date = models.DateField(blank=True, null=True, db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    customized = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.academic_calendar, self.offer_year)


def save(academic_cal):
    """
    It creates an event in the academic calendar of each annual offer when an
    event is created in the academic calendar.
    """
    academic_yr = academic_cal.academic_year
    offer_year_list = offer_year.find_by_academic_year(academic_yr.id)
    for offer_yr in offer_year_list:
        offer_yr_calendar = OfferYearCalendar()
        offer_yr_calendar.academic_calendar = academic_cal
        offer_yr_calendar.offer_year = offer_yr
        offer_yr_calendar.start_date = academic_cal.start_date
        offer_yr_calendar.end_date = academic_cal.end_date
        offer_yr_calendar.save()


def update(academic_cal):
    sent_message_error = None
    offer_year_calendar_list = find_by_academic_calendar(academic_cal)
    if offer_year_calendar_list:
        for offer_year_calendar in offer_year_calendar_list:
            if offer_year_calendar.customized: # case offerYearCalendar is already customized
                # We update the new start date
                # WARNING : this is TEMPORARY ; a solution for the sync from EPC to OSIS
                #           because the start_date for scores_encodings doesn't exist in EPC
                offer_year_calendar.start_date = academic_cal.start_date
                offer_year_calendar.save()
            else:
                offer_year_calendar.start_date = academic_cal.start_date
                offer_year_calendar.end_date = academic_cal.end_date
                offer_year_calendar.save()
    else:
        save(academic_cal)
    return sent_message_error


def offer_year_calendar_by_current_session_exam():
    return OfferYearCalendar.objects.filter(start_date__lte=timezone.now()) \
                                    .filter(end_date__gte=timezone.now()).first()


def find_by_academic_calendar(academic_cal):
    return OfferYearCalendar.objects.filter(academic_calendar=int(academic_cal.id))


def find_offer_year_calendar(offer_yr):
    return OfferYearCalendar.objects.filter(offer_year=offer_yr,
                                            start_date__isnull=False,
                                            end_date__isnull=False).order_by('start_date',
                                                                             'academic_calendar__title')


def find_offer_year_calendars_by_academic_year(academic_yr):
    return OfferYearCalendar.objects.filter(academic_calendar__academic_year=academic_yr)\
                                    .order_by('academic_calendar', 'offer_year__acronym')


def find_by_id(offer_year_calendar_id):
    return OfferYearCalendar.objects.get(pk=offer_year_calendar_id)


def find_deliberation_date(offer_year, session_number):
    title = 'Deliberations - exam session ' + str(session_number)
    queryset = OfferYearCalendar.objects.filter(academic_calendar__title=title)\
                                        .filter(offer_year=offer_year)\
                                        .values('start_date')
    if len(queryset) == 1:
        return queryset[0].get('start_date')
    return None


def get_min_start_date(academic_calendar_id):
    return OfferYearCalendar.objects.filter(academic_calendar_id=academic_calendar_id) \
                                    .filter(customized=True) \
                                    .filter(start_date__isnull=False)\
                                    .earliest('start_date')


def get_max_end_date(academic_calendar_id):
    return OfferYearCalendar.objects.filter(academic_calendar_id=academic_calendar_id) \
                                    .filter(customized=True) \
                                    .filter(end_date__isnull=False) \
                                    .latest('end_date')