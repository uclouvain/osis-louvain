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
from typing import List

import attr
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.db.models.query import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums import academic_calendar_type
from base.models.learning_unit_year import LearningUnitYear


@attr.s(frozen=True, slots=True)
class AcademicEvent:
    title = attr.ib(type=str)
    authorized_target_year = attr.ib(type=int)
    start_date = attr.ib(type=datetime.date)
    end_date = attr.ib(type=datetime.date)

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
            AcademicEventFactory().get_academic_events(self.event_reference),
            key=lambda academic_event: academic_event.start_date
        )

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        """
        This function will be called by a Celery job in order to ensure that event exist to N + 6.
        This function must be implemented in idempotent way.
        """
        raise NotImplementedError()


class AcademicEventFactory:
    def get_academic_events(self, event_reference: str) -> List[AcademicEvent]:
        qs = AcademicCalendar.objects.filter(
            reference=event_reference
        ).annotate(
            authorized_target_year=F('data_year__year')
        ).values('title', 'start_date', 'end_date', 'authorized_target_year')
        return [AcademicEvent(**obj) for obj in qs]


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

    @cached_property
    def _get_academic_events(self) -> List[AcademicSessionEvent]:
        return sorted(
            AcademicEventSessionFactory().get_academic_session_events(self.event_reference),
            key=lambda academic_session_event: academic_session_event.start_date
        )


class AcademicEventSessionFactory:
    def get_academic_session_events(self, event_reference: str) -> List[AcademicSessionEvent]:
        qs = AcademicCalendar.objects.filter(
            reference=event_reference
        ).exclude(
            sessionexamcalendar__isnull=True
        ).annotate(
            authorized_target_year=F('data_year__year'),
            session=F('sessionexamcalendar__number_session')
        ).values('title', 'start_date', 'end_date', 'authorized_target_year', 'session')
        return [AcademicSessionEvent(**obj) for obj in qs]


class EventPerm(ABC):
    academic_year_field = 'academic_year'
    model = None  # To instantiate == ex : EducationGroupYear
    event_reference = None  # To instantiate == ex : academic_calendar_type.EDUCATION_GROUP_EDITION
    obj = None  # To instantiate
    raise_exception = True
    error_msg = ""  # To instantiate == ex : _("This education group is not editable during this period.")

    def __init__(self, obj=None, raise_exception=True):
        if self.model and obj and not isinstance(obj, self.model):
            raise AttributeError("The provided obj must be a {}".format(self.model.__name__))
        self.obj = obj
        self.raise_exception = raise_exception

    def is_open(self):
        if self.obj:
            return self._is_open_for_specific_object()
        return self._is_calendar_opened()

    @classmethod
    def get_open_academic_calendars_queryset(cls) -> QuerySet:
        qs = AcademicCalendar.objects.open_calendars()
        if cls.event_reference:
            qs = qs.filter(reference=cls.event_reference)
        return qs

    @classmethod
    def get_academic_calendars_queryset(cls, data_year) -> QuerySet:
        qs = AcademicCalendar.objects.filter(data_year=data_year)
        if cls.event_reference:
            qs = qs.filter(reference=cls.event_reference)
        return qs

    @cached_property
    def open_academic_calendars_for_specific_object(self) -> list:
        obj_ac_year = getattr(self.obj, self.academic_year_field)
        return list(self.get_open_academic_calendars_queryset().filter(data_year=obj_ac_year))

    def _is_open_for_specific_object(self) -> bool:
        if not self.open_academic_calendars_for_specific_object:
            if self.raise_exception:
                raise PermissionDenied(_(self.error_msg).capitalize())
            return False
        return True

    @classmethod
    def _is_calendar_opened(cls) -> bool:
        return cls.get_open_academic_calendars_queryset().exists()

    @classmethod
    def get_academic_years(cls, min_academic_y=None, max_academic_y=None) -> QuerySet:
        return AcademicYear.objects.filter(
            pk__in=cls.get_academic_years_ids(min_academic_y=min_academic_y, max_academic_y=max_academic_y)
        )

    @classmethod
    def get_academic_years_ids(cls, min_academic_y=None, max_academic_y=None) -> QuerySet:
        qs = cls.get_open_academic_calendars_queryset()
        if min_academic_y:
            qs = qs.filter(data_year__year__gte=min_academic_y)
        if max_academic_y:
            qs = qs.filter(data_year__year__lte=max_academic_y)
        return qs.values_list('data_year', flat=True)


class EventPermClosed(EventPerm):
    def is_open(self):
        return False

    @classmethod
    def get_open_academic_calendars_queryset(cls) -> QuerySet:
        return AcademicCalendar.objects.none()


class EventPermLearningUnitFacultyManagerEdition(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.LEARNING_UNIT_EDITION_FACULTY_MANAGERS
    error_msg = _("This learning unit is not editable by faculty managers during this period.")


class EventPermLearningUnitCentralManagerEdition(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.LEARNING_UNIT_EDITION_CENTRAL_MANAGERS
    error_msg = _("This learning unit is not editable by central managers during this period.")


# TODO : gather EventPerm disregarding role
def generate_event_perm_learning_unit_edition(person, obj=None, raise_exception=True):
    if person.is_central_manager_for_ue:
        return EventPermLearningUnitCentralManagerEdition(obj, raise_exception)
    elif person.is_faculty_manager_for_ue:
        return EventPermLearningUnitFacultyManagerEdition(obj, raise_exception)
    else:
        return EventPermClosed(obj, raise_exception)


class EventPermCreationOrEndDateProposalCentralManager(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_CENTRAL_MANAGERS
    error_msg = _("Creation or end date modification proposal not allowed for central managers during this period.")


class EventPermCreationOrEndDateProposalFacultyManager(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_FACULTY_MANAGERS
    error_msg = _("Creation or end date modification proposal not allowed for faculty managers during this period.")


def generate_event_perm_creation_end_date_proposal(person, obj=None, raise_exception=True):
    if person.is_central_manager:
        return EventPermCreationOrEndDateProposalCentralManager(obj, raise_exception)
    elif person.is_faculty_manager:
        return EventPermCreationOrEndDateProposalFacultyManager(obj, raise_exception)
    else:
        return EventPermClosed(obj, raise_exception)


class EventPermModificationOrTransformationProposalCentralManager(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_CENTRAL_MANAGERS
    error_msg = _("Modification or transformation proposal not allowed for central managers during this period.")


class EventPermModificationOrTransformationProposalFacultyManager(EventPerm):
    model = LearningUnitYear
    event_reference = academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_FACULTY_MANAGERS
    error_msg = _("Modification or transformation proposal not allowed for faculty managers during this period.")


def generate_event_perm_modification_transformation_proposal(person, obj=None, raise_exception=True):
    if person.is_central_manager:
        return EventPermModificationOrTransformationProposalCentralManager(obj, raise_exception)
    elif person.is_faculty_manager:
        return EventPermModificationOrTransformationProposalFacultyManager(obj, raise_exception)
    else:
        return EventPermClosed(obj, raise_exception)
