##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from base.models import academic_year


class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ('title', 'academic_year', 'start_date', 'end_date', 'changed')
    fieldsets = ((None, {'fields': ('academic_year', 'title', 'description', 'start_date', 'end_date')}),)


class AcademicCalendar(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    academic_year = models.ForeignKey('AcademicYear')
    title = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    highlight_title = models.CharField(max_length=255, blank=True, null=True)
    highlight_description = models.CharField(max_length=255, blank=True, null=True)
    highlight_shortcut = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return u"%s %s" % (self.academic_year, self.title)


def find_highlight_academic_calendars():
    return AcademicCalendar.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(),
                                           highlight_title__isnull=False, highlight_description__isnull=False,
                                           highlight_shortcut__isnull=False)


def find_academic_calendar_by_academic_year(academic_year_id):
    return AcademicCalendar.objects.filter(academic_year=academic_year_id).order_by('title')


def find_academic_calendar_by_academic_year_with_dates(academic_year_id):
    now = timezone.now()
    return AcademicCalendar.objects.filter(academic_year=academic_year_id,
                                           start_date__isnull=False,
                                           end_date__isnull=False) \
                                   .filter(models.Q(start_date__lte=now, end_date__gte=now) |
                                           models.Q(start_date__gte=now, end_date__gte=now)) \
                                   .order_by('start_date')


def find_academic_calendar_by_id(academic_calendar_id):
    return AcademicCalendar.objects.get(pk=academic_calendar_id)
