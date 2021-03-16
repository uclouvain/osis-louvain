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
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from reversion.admin import VersionAdmin

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.exceptions import StartDateHigherThanEndDateException
from base.models.utils.admin_extentions import remove_delete_action
from base.signals.publisher import compute_all_scores_encodings_deadlines
from osis_common.models import osis_model_admin
from osis_common.utils.models import get_object_or_none


class AcademicCalendarAdmin(VersionAdmin, osis_model_admin.OsisModelAdmin):
    list_display = ('title', 'data_year', 'start_date', 'end_date',)
    list_display_links = ('title', 'data_year')
    readonly_fields = ('title', )
    list_filter = ('reference', 'data_year')
    search_fields = ['title']
    ordering = ('start_date',)
    actions = ['send_calendar_reminder_notice']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return remove_delete_action(super(AcademicCalendarAdmin, self).get_actions(request))

    def send_calendar_reminder_notice(self, request, queryset):
        from base.tasks import calendar_reminder_notice
        return calendar_reminder_notice.run()
    send_calendar_reminder_notice.short_description = _("Send calendar reminder notice")


class AcademicCalendarQuerySet(models.QuerySet):
    def open_calendars(self, date=None):
        """ return only open calendars """
        if not date:
            date = timezone.now()

        return self.filter(start_date__lte=date, end_date__gt=date)


class AcademicCalendar(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT)
    data_year = models.ForeignKey(
        'AcademicYear', on_delete=models.PROTECT, related_name='related_academic_calendar_data', blank=True, null=True
    )
    title = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    highlight_title = models.CharField(max_length=50, blank=True, null=True)
    highlight_description = models.CharField(max_length=255, blank=True, null=True)
    highlight_shortcut = models.CharField(max_length=255, blank=True, null=True)
    reference = models.CharField(choices=AcademicCalendarTypes.choices(), max_length=70)

    objects = AcademicCalendarQuerySet.as_manager()

    def save(self, *args, **kwargs):
        self.validation_mandatory_dates()
        self.validation_start_end_dates()
        super().save(*args, **kwargs)
        compute_all_scores_encodings_deadlines.send(sender=self.__class__, academic_calendar=self)

    def validation_start_end_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise StartDateHigherThanEndDateException(_('End date must be lower than start date'))

    def validation_mandatory_dates(self):
        if self.start_date is None:
            raise AttributeError(_('Start date is mandatory'))

    def __str__(self):
        return "{} {}".format(self.academic_year, self.title)

    class Meta:
        permissions = (
            ("can_access_academic_calendar", "Can access academic calendar"),
        )
        unique_together = ("data_year", "title")


def find_highlight_academic_calendar():
    return AcademicCalendar.objects.open_calendars() \
        .exclude(highlight_title__isnull=True).exclude(highlight_title__exact='') \
        .exclude(highlight_description__isnull=True).exclude(highlight_description__exact='') \
        .exclude(highlight_shortcut__isnull=True).exclude(highlight_shortcut__exact='') \
        .order_by('end_date')


def get_by_reference_and_data_year(a_reference, data_year):
    return get_object_or_none(AcademicCalendar, reference=a_reference, data_year=data_year)
