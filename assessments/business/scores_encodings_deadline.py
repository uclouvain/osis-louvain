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
import logging

from django.conf import settings

from base.models import session_exam_calendar, offer_year_calendar
from base.models.enums import academic_calendar_type as ac_type
from base.models.session_exam_deadline import SessionExamDeadline

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def recompute_all_deadlines(academic_calendar):
    if academic_calendar.reference == ac_type.SCORES_EXAM_SUBMISSION:
        for off_year_cal in academic_calendar.offeryearcalendar_set.all():
            compute_deadline(off_year_cal)


def compute_deadline_by_student(session_exam_deadline):
    # TODO :: replace usage of offer_year by education_group_year !
    off_year_calendar = offer_year_calendar.search(offer_year=session_exam_deadline.offer_enrollment.offer_year,
                                                   academic_calendar_reference=ac_type.DELIBERATION,
                                                   number_session=session_exam_deadline.number_session).first()
    if off_year_calendar:
        compute_deadline(off_year_calendar, session_exam_deadlines=[session_exam_deadline])
    else:
        msg = "No OfferYearCalendar found for OfferYear = {}, type = {} and number_session = {}"
        logger.warning(msg.format(session_exam_deadline.offer_enrollment.offer_year.acronym,
                                  ac_type.SCORES_EXAM_SUBMISSION,
                                  session_exam_deadline.number_session))


def compute_deadline(off_year_calendar, session_exam_deadlines=None):
    if not _impact_scores_encodings_deadlines(off_year_calendar):
        return

    oyc_deliberation = _find_by_reference(off_year_calendar, ac_type.DELIBERATION)
    oyc_scores_exam_submission = _find_by_reference(off_year_calendar, ac_type.SCORES_EXAM_SUBMISSION)

    end_date_offer_year = _one_day_before_deliberation_date(oyc_deliberation)
    tutor_submission_date = _get_end_date_value(oyc_scores_exam_submission)

    end_date_academic = oyc_scores_exam_submission.academic_calendar.end_date if oyc_scores_exam_submission else None
    if session_exam_deadlines is None:
        session_exam_deadlines = _get_list_sessions_exam_deadlines(off_year_calendar.academic_calendar,
                                                                   off_year_calendar.offer_year)
    _save_new_deadlines(session_exam_deadlines, end_date_academic, end_date_offer_year, tutor_submission_date)


def _get_end_date_value(off_year_cal):
    end_date = None
    if off_year_cal and off_year_cal.end_date:
        end_date = _get_date_instance(off_year_cal.end_date)
    return end_date


def _get_date_instance(date):
    if date and isinstance(date, datetime.datetime):
        date = date.date()
    return date


def _impact_scores_encodings_deadlines(oyc):
    return oyc.academic_calendar.reference in (ac_type.DELIBERATION, ac_type.SCORES_EXAM_SUBMISSION)


def _save_new_deadlines(sessions_exam_deadlines, end_date_academic, end_date_offer_year, tutor_submission_date):
    for sess_exam_deadline in sessions_exam_deadlines:
        end_date_student = _one_day_before(sess_exam_deadline.deliberation_date)

        new_deadline = min(filter(None, (_get_date_instance(end_date_academic),
                                         _get_date_instance(end_date_offer_year),
                                         _get_date_instance(end_date_student))))
        new_deadline_tutor = _compute_delta_deadline_tutor(new_deadline, tutor_submission_date)

        if _is_deadline_changed(sess_exam_deadline, new_deadline, new_deadline_tutor):
            sess_exam_deadline.deadline = new_deadline
            sess_exam_deadline.deadline_tutor = new_deadline_tutor
            sess_exam_deadline.save()


def _is_deadline_changed(sess_exam_deadline, new_deadline, new_deadline_tutor):
    return new_deadline != sess_exam_deadline.deadline or new_deadline_tutor != sess_exam_deadline.deadline_tutor


def _find_by_reference(off_year_calendar, reference):
    if reference == off_year_calendar.academic_calendar.reference:
        result = off_year_calendar
    else:
        result = _get_oyc_by_reference(off_year_calendar, reference)
    if not result:
        msg = "No OfferYearCalendar '{}' found for offerYear = {}"
        if off_year_calendar.offer_year:
            logger.warning(msg.format(ac_type.DELIBERATION, off_year_calendar.offer_year.acronym))
    return result


def _get_oyc_by_reference(off_year_calendar, reference):
    number_session = session_exam_calendar.get_number_session_by_academic_calendar(off_year_calendar.academic_calendar)
    if number_session:
        try:
            return offer_year_calendar.search(education_group_year=off_year_calendar.education_group_year,
                                              offer_year=off_year_calendar.offer_year,
                                              academic_calendar_reference=reference,
                                              number_session=number_session).get()
        except offer_year_calendar.OfferYearCalendar.DoesNotExist:
            return None


def _get_list_sessions_exam_deadlines(academic_calendar, offer_year):
    session_exam_deadlines = []
    number_session = session_exam_calendar.get_number_session_by_academic_calendar(academic_calendar)
    if number_session:
        session_exam_deadlines = SessionExamDeadline.objects.filter(
            offer_enrollment__offer_year=offer_year, number_session=number_session)
    else:
        msg = "No SessionExamCalendar (number session) found for academic calendar = {}"
        logger.warning(msg.format(academic_calendar.title))
    return session_exam_deadlines


def _one_day_before_deliberation_date(oyc):
    return _one_day_before(oyc.end_date) if oyc and oyc.end_date else None


def _one_day_before(current_date):
    result = None
    if current_date:
        current_date = _get_date_instance(current_date)
        result = current_date - datetime.timedelta(days=1)
    return result


def _compute_delta_deadline_tutor(deadline, tutor_submission_date):
    delta_tutor_deadline = 0
    if deadline and tutor_submission_date and deadline > tutor_submission_date:
            delta_tutor_deadline = (deadline - tutor_submission_date).days
    return delta_tutor_deadline
