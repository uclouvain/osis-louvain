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

from django.db import models

from base.models import offer_year_calendar, academic_year
from base.models.enums import number_session, academic_calendar_type
from osis_common.models.osis_model_admin import OsisModelAdmin


class SessionExamCalendarAdmin(OsisModelAdmin):
    list_display = ('academic_calendar', 'number_session', 'changed')
    list_filter = ('academic_calendar__academic_year', 'number_session', 'academic_calendar__reference')
    raw_id_fields = ('academic_calendar',)
    search_fields = ['academic_calendar__title']


class SessionExamCalendar(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    number_session = models.IntegerField(choices=number_session.NUMBERS_SESSION)
    academic_calendar = models.OneToOneField('AcademicCalendar', on_delete=models.CASCADE)

    def __str__(self):
        return u"%s - %s" % (self.academic_calendar, self.number_session)


def current_session_exam(date=None):
    try:
        if date is None:
            date = datetime.date.today()
        return SessionExamCalendar.objects.get(
            academic_calendar__start_date__lte=date,
            academic_calendar__end_date__gte=date,
            academic_calendar__reference=academic_calendar_type.SCORES_EXAM_SUBMISSION
        )
    except SessionExamCalendar.DoesNotExist:
        return None


def find_session_exam_number(date=None):
    if date is None:
        date = datetime.date.today()
    current_session = current_session_exam(date)
    if current_session:
        return current_session.number_session
    return None


def get_latest_session_exam(date=None):
    if date is None:
        date = datetime.date.today()
    current_academic_year = academic_year.current_academic_year()
    return SessionExamCalendar.objects.exclude(academic_calendar__end_date__isnull=True) \
        .filter(academic_calendar__end_date__lte=date,
                academic_calendar__academic_year=current_academic_year,
                academic_calendar__reference=academic_calendar_type.SCORES_EXAM_SUBMISSION) \
        .order_by('-academic_calendar__end_date') \
        .first()


def get_closest_new_session_exam(date=None):
    if date is None:
        date = datetime.date.today()
    current_academic_year = academic_year.current_academic_year()
    return SessionExamCalendar.objects.exclude(academic_calendar__start_date__isnull=True) \
        .filter(academic_calendar__start_date__gte=date,
                academic_calendar__academic_year=current_academic_year,
                academic_calendar__reference=academic_calendar_type.SCORES_EXAM_SUBMISSION) \
        .order_by('academic_calendar__start_date') \
        .first()


def find_deliberation_date(nb_session, offer_year):
    """"
    :param nb_session The number of session research
    :param offer_year The offer year research
    :return the deliberation date of the offer and session
    """
    session_exam_cals = SessionExamCalendar.objects.filter(
        number_session=nb_session,
        academic_calendar__reference=academic_calendar_type.DELIBERATION
    )
    academic_cals_id = [session_exam.academic_calendar_id for session_exam in list(session_exam_cals)]

    if academic_cals_id:
        offer_year_cal = offer_year_calendar.find_by_offer_year(offer_yr=offer_year) \
            .filter(academic_calendar__in=academic_cals_id) \
            .first()
        return offer_year_cal.start_date

    return None


# FIXME: Only used in tests
def find_by_session_and_academic_year(nb_session, an_academic_year):
    return SessionExamCalendar.objects.filter(
        number_session=nb_session,
        academic_calendar__academic_year=an_academic_year
    )


def get_number_session_by_academic_calendar(academic_calendar):
    session = getattr(academic_calendar, 'sessionexamcalendar', None)
    return session.number_session if session else None
