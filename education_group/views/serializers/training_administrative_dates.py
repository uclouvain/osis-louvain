##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import datetime
from typing import Dict, List

from django.db.models import F

from base.models.enums import academic_calendar_type
from base.models.offer_year_calendar import OfferYearCalendar

DomainTitle = str
SessionNumber = str
Dates = Dict[str, datetime]


class AdministrativeDateBySession:
    def __init__(self, domain_title: str, session_number: int, start_date: datetime, end_date: datetime):
        self.domain_title = domain_title
        self.session_number = session_number
        self.start_date = start_date
        self.end_date = end_date


def get_session_dates(offer_acronym: str, year: int) -> Dict[DomainTitle, Dict[SessionNumber, Dates]]:
    dates = __get_queryset_values(offer_acronym, year)
    return {
        'exam_enrollments_dates': __get_dates_by_session(academic_calendar_type.EXAM_ENROLLMENTS, dates),
        'scores_exam_submission_dates': __get_dates_by_session(academic_calendar_type.SCORES_EXAM_SUBMISSION, dates),
        'dissertations_submission_dates': __get_dates_by_session(academic_calendar_type.DISSERTATION_SUBMISSION, dates),
        'deliberations_dates': __get_dates_by_session(academic_calendar_type.DELIBERATION, dates),
        'scores_exam_diffusion_dates': __get_dates_by_session(academic_calendar_type.SCORES_EXAM_DIFFUSION, dates),
    }


def __get_dates_by_session(domain_title: str, dates: List[AdministrativeDateBySession]) -> Dict[SessionNumber, Dates]:
    dates = list(filter(lambda administrative_date: administrative_date.domain_title == domain_title, dates))
    return {
        'session1': __get_session_dates(1, dates),
        'session2': __get_session_dates(2, dates),
        'session3': __get_session_dates(3, dates),
    }


def __get_session_dates(session_number: int, dates: List[AdministrativeDateBySession]) -> Dates:
    administrative_date = next((date for date in dates if date.session_number == session_number), None)
    start_date = administrative_date.start_date if administrative_date else None
    end_date = administrative_date.end_date if administrative_date else None
    return {
        'start_date': start_date,
        'end_date': end_date,
    }


def __get_queryset_values(offer_acronym: str, year: int) -> List[AdministrativeDateBySession]:
    calendar_types_to_fetch = (
        academic_calendar_type.EXAM_ENROLLMENTS,
        academic_calendar_type.SCORES_EXAM_SUBMISSION,
        academic_calendar_type.DISSERTATION_SUBMISSION,
        academic_calendar_type.DELIBERATION,
        academic_calendar_type.SCORES_EXAM_DIFFUSION
    )
    qs = OfferYearCalendar.objects.filter(
        education_group_year__acronym=offer_acronym,
        education_group_year__academic_year__year=year,
        academic_calendar__reference__in=calendar_types_to_fetch,
    ).annotate(
        session_number=F('academic_calendar__sessionexamcalendar__number_session'),
        domain_title=F('academic_calendar__reference'),
    ).values('session_number', 'start_date', 'end_date', 'domain_title')
    return [
        AdministrativeDateBySession(
            domain_title=values['domain_title'],
            session_number=values['session_number'],
            start_date=values['start_date'],
            end_date=values['end_date'],
        )
        for values in qs
    ]
