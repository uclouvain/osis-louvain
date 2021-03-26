import datetime
from typing import Tuple, List

import numpy as np
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from backoffice.celery import app as celery_app
from base.business.academic_calendar import AcademicEventRepository, AcademicEvent
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.messaging import message_config, send_message as message_service


@celery_app.task
def run() -> dict:
    """
    This job will notify team members via email that an event will begin soon.
    """
    event_types_monitored = (
        AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
        AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
        AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name,
        AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION.name,
        AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE.name,
    )
    receiver_emails = settings.ACADEMIC_CALENDAR_REMINDER_EMAILS
    if not receiver_emails:
        raise ImproperlyConfigured("Missing ACADEMIC_CALENDAR_REMINDER_EMAILS settings")

    academic_events_to_remind = _get_academic_events_to_remind(event_types_monitored)
    if academic_events_to_remind:
        _send_reminder_mail(receiver_emails, academic_events_to_remind)
    return {'Academic events reminder notice': len(academic_events_to_remind)}


def _get_academic_events_to_remind(event_types_monitored: Tuple) -> List[AcademicEvent]:
    return [
        academic_event for academic_event in AcademicEventRepository().get_academic_events() if
        academic_event.type in event_types_monitored and _is_due_date_reached(academic_event)
    ]


def _is_due_date_reached(academic_event: AcademicEvent):
    """
    Due date is reached when 5 working days and 1 working day before start date of event
    """
    working_days_left = np.busday_count(datetime.date.today(), academic_event.start_date)
    return working_days_left == 5 or working_days_left == 1


def _send_reminder_mail(receiver_emails: List[str], academic_events: List[AcademicEvent]):
    html_template_ref = 'calendar_reminder_notice_html'
    txt_template_ref = 'calendar_reminder_notice_txt'

    receivers = [
        message_config.create_receiver(None, email, settings.LANGUAGE_CODE_FR)
        for email in receiver_emails
    ]

    template_base_data = {'academic_events': academic_events}
    message_content = message_config.create_message_content(
        html_template_ref,
        txt_template_ref,
        None,
        receivers,
        template_base_data,
        {},
        None
    )
    return message_service.send_messages(message_content)
