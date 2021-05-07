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
import datetime
from typing import Optional

from base.business.academic_calendar import AcademicEventSessionCalendarHelper, AcademicSessionEvent
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.session_exam_calendar import SessionExamCalendar

FIRST_SESSION = 1


class ScoresExamSubmissionCalendar(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name

    def get_closest_academic_event(self, date=None) -> Optional[AcademicSessionEvent]:
        opened_academic_events = self.get_opened_academic_events(date)
        if opened_academic_events:
            return opened_academic_events[0]

        next_academic_event = self.get_next_academic_event(date)
        if next_academic_event and next_academic_event.session != FIRST_SESSION:
            return next_academic_event
        return None

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        current_academic_year = AcademicYear.objects.current()
        academic_years = AcademicYear.objects.min_max_years(current_academic_year.year, current_academic_year.year + 6)

        for ac_year in academic_years:
            cls._create_session_one(ac_year)
            cls._create_session_two(ac_year)
            cls._create_session_three(ac_year)

    @classmethod
    def _create_session_one(cls, academic_year: AcademicYear):
        kwargs = {
            'reference': cls.event_reference,
            'data_year': academic_year,
            'sessionexamcalendar__number_session': 1
        }

        if not AcademicCalendar.objects.filter(**kwargs).exists():
            academic_calendar = AcademicCalendar.objects.create(
                reference=cls.event_reference,
                data_year=academic_year,
                title="Encodage de notes - Session 1",
                start_date=datetime.date(academic_year.year, 12, 15),
                end_date=datetime.date(academic_year.year + 1, 2, 28),
            )
            SessionExamCalendar.objects.create(number_session=1, academic_calendar=academic_calendar)

    @classmethod
    def _create_session_two(cls, academic_year: AcademicYear):
        kwargs = {
            'reference': cls.event_reference,
            'data_year': academic_year,
            'sessionexamcalendar__number_session': 2
        }

        if not AcademicCalendar.objects.filter(**kwargs).exists():
            academic_calendar = AcademicCalendar.objects.create(
                reference=cls.event_reference,
                data_year=academic_year,
                title="Encodage de notes - Session 2",
                start_date=datetime.date(academic_year.year + 1, 5, 20),
                end_date=datetime.date(academic_year.year + 1, 7, 10),
            )
            SessionExamCalendar.objects.create(number_session=2, academic_calendar=academic_calendar)

    @classmethod
    def _create_session_three(cls, academic_year: AcademicYear):
        kwargs = {
            'reference': cls.event_reference,
            'data_year': academic_year,
            'sessionexamcalendar__number_session': 3
        }
        if not AcademicCalendar.objects.filter(**kwargs).exists():
            academic_calendar = AcademicCalendar.objects.create(
                reference=cls.event_reference,
                data_year=academic_year,
                title="Encodage de notes - Session 3",
                start_date=datetime.date(academic_year.year + 1, 8, 10),
                end_date=datetime.date(academic_year.year + 1, 9, 15),
            )
            SessionExamCalendar.objects.create(number_session=3, academic_calendar=academic_calendar)
