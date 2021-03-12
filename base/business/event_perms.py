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
from abc import ABC
from typing import List, Optional

import attr
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear


@attr.s(frozen=True, slots=True)
class AcademicEvent:
    id = attr.ib(type=int)
    title = attr.ib(type=str)
    authorized_target_year = attr.ib(type=int)
    start_date = attr.ib(type=datetime.date)
    end_date = attr.ib(type=datetime.date)
    type = attr.ib(type=str)

    def is_open_now(self) -> bool:
        """
        Returns True only if this event is open right now
        """
        date = datetime.date.today()
        return self.is_open(date)

    def is_open(self, date) -> bool:
        """
        Returns True only if this event is open on the date specified
        """
        return self.start_date <= date and (self.end_date is None or self.end_date >= date)

    def is_target_year_authorized(self, target_year: int) -> bool:
        return self.authorized_target_year == target_year


class AcademicEventCalendarHelper(ABC):
    event_reference = None

    def is_target_year_authorized(self, target_year: int = None) -> bool:
        """
        Check if the target year provided in kwargs is authorized to modification.
        If no target_year provided, it check if there is at least on year authorized to modification today
        """
        target_years_opened = self.get_target_years_opened()
        if target_year is None:
            return bool(target_years_opened)
        return bool(next((year for year in target_years_opened if year == target_year), False))

    def get_target_years_opened(self, date=None) -> List[int]:
        """
        Return list of year authorized according to a date provided in kwargs.
        If no date provided, it will assume as today
        """
        if date is None:
            date = datetime.date.today()
        return sorted([
            academic_event.authorized_target_year for academic_event in self._get_academic_events
            if academic_event.is_open(date)
        ])

    def get_opened_academic_events(self, date=None) -> List[AcademicEvent]:
        """
        Return all current academic event opened based on date provided in kwargs
        If no date provided, it will assume as today
        """
        if date is None:
            date = datetime.date.today()
        return [academic_event for academic_event in self._get_academic_events if academic_event.is_open(date)]

    def get_next_academic_event(self, date=None) -> AcademicEvent:
        """
        Return next academic event based on date provided in kwargs
        If no date provided, it will assume as today
        """
        if date is None:
            date = datetime.date.today()

        events_filtered = [
            event for event in self._get_academic_events
            if event.end_date is None or event.end_date > date
        ]
        return events_filtered[0] if events_filtered else None

    def get_previous_academic_event(self, date=None) -> AcademicEvent:
        """
        Return previous academic event based on date provided in kwargs
        If no date provided, it will assume as today
        """
        if date is None:
            date = datetime.date.today()

        events_filtered = [
            event for event in self._get_academic_events if
            event.end_date is not None and event.end_date < date
        ]
        return events_filtered[-1] if events_filtered else None

    def get_academic_event(self, target_year: int) -> AcademicEvent:
        """
        Return academic event related to target_year provided
        """
        return next(
            (academic_event for academic_event in self._get_academic_events
             if academic_event.authorized_target_year == target_year
             ),
            None
        )

    @cached_property
    def _get_academic_events(self) -> List[AcademicEvent]:
        return sorted(
            AcademicEventRepository().get_academic_events(self.event_reference),
            key=lambda academic_event: academic_event.start_date
        )

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        """
        This function will be called by a Celery job in order to ensure that event exist to N + 6.
        This function must be implemented in idempotent way.
        """
        raise NotImplementedError()


class AcademicEventRepository:
    def get_academic_events(self, event_reference: Optional[str] = None) -> List[AcademicEvent]:
        qs = AcademicCalendar.objects.all()
        if event_reference:
            qs = qs.filter(reference=event_reference)
        qs = qs.annotate(
            authorized_target_year=F('data_year__year'),
            type=F('reference')
        ).values('id', 'title', 'start_date', 'end_date', 'authorized_target_year', 'type')
        return [AcademicEvent(**obj) for obj in qs]

    def get(self, academic_event_id: int) -> AcademicEvent:
        obj = AcademicCalendar.objects.annotate(
            authorized_target_year=F('data_year__year'),
            type=F('reference')
        ).values('id', 'title', 'start_date', 'end_date', 'authorized_target_year', 'type')\
         .get(pk=academic_event_id)
        return AcademicEvent(**obj)

    def update(self, academic_event: AcademicEvent):
        academic_event_db = AcademicCalendar.objects.get(pk=academic_event.id)
        academic_event_db.start_date = academic_event.start_date
        academic_event_db.end_date = academic_event.end_date
        academic_event_db.save()


@attr.s(frozen=True, slots=True)
class AcademicSessionEvent(AcademicEvent):
    session = attr.ib(type=int)


class AcademicEventSessionCalendarHelper(AcademicEventCalendarHelper):
    def get_academic_session_event(self, target_year: int, session: int) -> AcademicSessionEvent:
        """
        Return academic session event related to target_year and session provided
        """
        return next(
            (academic_session_event for academic_session_event in self._get_academic_events
             if academic_session_event.authorized_target_year == target_year and
                academic_session_event.session == session
             ),
            None
        )

    def get_opened_academic_events(self, date=None) -> List[AcademicSessionEvent]:
        return super().get_opened_academic_events(date=date)

    def get_previous_academic_event(self, date=None) -> AcademicSessionEvent:
        return super().get_previous_academic_event(date=date)

    def get_next_academic_event(self, date=None) -> AcademicSessionEvent:
        return super().get_next_academic_event(date=date)

    @cached_property
    def _get_academic_events(self) -> List[AcademicSessionEvent]:
        return sorted(
            AcademicEventSessionRepository().get_academic_session_events(self.event_reference),
            key=lambda academic_session_event: academic_session_event.start_date
        )


class AcademicEventSessionRepository:
    def get_academic_session_events(self, event_reference: str) -> List[AcademicSessionEvent]:
        qs = AcademicCalendar.objects.filter(
            reference=event_reference
        ).exclude(
            sessionexamcalendar__isnull=True
        ).annotate(
            authorized_target_year=F('data_year__year'),
            type=F('reference'),
            session=F('sessionexamcalendar__number_session')
        ).values('id', 'title', 'start_date', 'end_date', 'authorized_target_year', 'type', 'session')
        return [AcademicSessionEvent(**obj) for obj in qs]
