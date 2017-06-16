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
from django.db import models
from django.utils import timezone
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from base.models.exceptions import FunctionArgumentMissingException, StartDateHigherThanEndDateException
from base.models.enums import academic_calendar_type
from django.utils.translation import ugettext as _
from base.models.utils.admin_extentions import remove_delete_action


FUNCTIONS = 'functions'


class AcademicCalendarAdmin(SerializableModelAdmin):
    list_display = ('academic_year', 'title', 'start_date', 'end_date')
    list_display_links = None
    readonly_fields = ('academic_year', 'title', 'start_date', 'end_date')
    list_filter = ('academic_year',)
    search_fields = ['title']
    ordering = ('start_date',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return remove_delete_action(super(AcademicCalendarAdmin, self).get_actions(request))


class AcademicCalendar(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    academic_year = models.ForeignKey('AcademicYear')
    title = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    highlight_title = models.CharField(max_length=255, blank=True, null=True)
    highlight_description = models.CharField(max_length=255, blank=True, null=True)
    highlight_shortcut = models.CharField(max_length=255, blank=True, null=True)
    reference = models.CharField(choices=academic_calendar_type.ACADEMIC_CALENDAR_TYPES, max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        if FUNCTIONS not in kwargs.keys():
            raise FunctionArgumentMissingException('The kwarg "{0}" must be set.'.format(FUNCTIONS))
        functions = kwargs.pop(FUNCTIONS)
        self.validation_mandatory_dates()
        self.validation_start_end_dates()
        super(AcademicCalendar, self).save(*args, **kwargs)
        for function in functions:
            function(self)

    def validation_start_end_dates(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise StartDateHigherThanEndDateException(_('end_start_date_error'))

    def validation_mandatory_dates(self):
        if self.start_date is None or self.end_date is None:
            raise AttributeError(_('dates_mandatory_error'))

    def __str__(self):
        return u"%s %s" % (self.academic_year, self.title)

    class Meta:
        permissions = (
            ("can_access_academic_calendar", "Can access academic calendar"),
        )


def find_highlight_academic_calendar():
    return AcademicCalendar.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(),
                                           highlight_title__isnull=False, highlight_description__isnull=False,
                                           highlight_shortcut__isnull=False).order_by('end_date').first()


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


def find_by_id(academic_calendar_id):
    try:
        return AcademicCalendar.objects.get(pk=academic_calendar_id)
    except AcademicCalendar.DoesNotExist:
        return None


def find_by_ids(academic_calendars_id):
    return AcademicCalendar.objects.filter(pk__in=academic_calendars_id)
