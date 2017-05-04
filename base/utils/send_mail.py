##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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

"""
Utility files for mail sending
"""

from django.utils.translation import ugettext as _

from osis_common.models import message_history as message_history_mdl
from osis_common.messaging import message_config, send_message as message_service
from base.models import person as person_mdl
from base.models import exam_enrollment as exam_enrollment_mdl
from osis_common.document import paper_sheet


def send_mail_after_scores_submission(persons, learning_unit_name, submitted_enrollments, all_encoded):
    """
    Send an email to all the teachers after the scores submission for a learning unit
    :param persons: The list of the teachers of the leaning unit
    :param learning_unit_name: The name of the learning unit for which scores were submitted
    :param submitted_enrollments : The list of newly sibmitted enrollments
    :param all_encoded : Tell if all the scores are encoded and submitted
    :return An error message if the template is not in the database
    """

    html_template_ref = 'assessments_scores_submission_html'
    txt_template_ref = 'assessments_scores_submission_txt'
    receivers = [message_config.create_receiver(person.id, person.email, person.language) for person in persons]
    suject_data = {'learning_unit_name': learning_unit_name}
    template_base_data = {'learning_unit_name': learning_unit_name,
                          'encoding_status':    _('encoding_status_ended') if all_encoded
                          else _('encoding_status_notended')
                          }
    header_txt = ['acronym', 'sessionn', 'registration_number', 'lastname', 'firstname', 'score', 'documentation']
    submitted_enrollments_data = [
        (
            enrollment.learning_unit_enrollment.offer_enrollment.offer_year.acronym,
            enrollment.session_exam.number_session,
            enrollment.learning_unit_enrollment.offer_enrollment.student.registration_id,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.last_name,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.first_name,
            enrollment.score_final,
            _(enrollment.justification_final) if enrollment.justification_final else None,
        ) for enrollment in submitted_enrollments]
    table = message_config.create_table('submitted_enrollments', header_txt, submitted_enrollments_data)

    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, [table], receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_after_academic_calendar_changes(academic_calendar, offer_year_calendar, programm_managers):
    """
    Send an email to all the programme manager after changes has been made on a offer_year_calendar with customized
    = True
    :param academic_calendar:
    :param offer_year_calendar:
    :param programm_managers:
    :return un error message if the template does not exists.
    """

    html_template_ref = 'academic_calendar_changes_html'
    txt_template_ref = 'academic_calendar_changes_txt'
    receivers = [message_config.create_receiver(manager.person.id, manager.person.email, manager.person.language)
                 for manager in programm_managers]
    suject_data = {'offer_year':            str(offer_year_calendar.offer_year.acronym),
                   'academic_calendar':     str(academic_calendar)}
    template_base_data = {
        'offer_year_title': offer_year_calendar.offer_year.title,
        'offer_year_acronym': offer_year_calendar.offer_year.acronym,
        'academic_calendar': str(academic_calendar),
    }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref,
                                                            None, receivers, template_base_data, suject_data)

    return message_service.send_messages(message_content)


def send_message_after_all_encoded_by_manager(persons, enrollments, learning_unit_acronym, offer_acronym):
    """
    Send a message to all tutor from a learning unit when all scores are submitted by program manager
    :param persons: The list of the tutor (person) of the learning unit
    :param enrollments: The enrollments that are encoded and submitted
    :param learning_unit_acronym The learning unit encoded
    :param offer_acronym: The offer which is managed
    :return: A message if an error occured, None if it's ok
    """

    html_template_ref = 'assessments_all_scores_by_pgm_manager_html'
    txt_template_ref = 'assessments_all_scores_by_pgm_manager_txt'
    receivers = [message_config.create_receiver(person.id, person.email, person.language) for person in persons]
    suject_data = {
        'learning_unit_acronym': learning_unit_acronym,
        'offer_acronym':         offer_acronym
    }
    template_base_data = {
        'learning_unit_acronym':    learning_unit_acronym,
        'offer_acronym':            offer_acronym,
    }
    enrollments_data = [
        (
            enrollment.learning_unit_enrollment.offer_enrollment.offer_year.acronym,
            enrollment.session_exam.number_session,
            enrollment.learning_unit_enrollment.offer_enrollment.student.registration_id,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.last_name,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.first_name,
            enrollment.score_final,
            _(enrollment.justification_final) if enrollment.justification_final else None,
        ) for enrollment in enrollments]
    enrollments_headers = (
        'acronym',
        'sessionn',
        'registration_number',
        'lastname',
        'firstname',
        'score',
        'documentation'
    )
    table = message_config.create_table('enrollments', enrollments_headers, enrollments_data)
    attachment = build_scores_sheet_attachment(enrollments)
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref,
                                                            [table], receivers, template_base_data, suject_data,
                                                            attachment)
    return message_service.send_messages(message_content)


def build_scores_sheet_attachment(list_exam_enrollments):
    name = "%s.pdf" % _('scores_sheet')
    mimetype = "application/pdf"
    content = paper_sheet.build_pdf(exam_enrollment_mdl.scores_sheet_data(list_exam_enrollments, tutor=None))
    return (name, content, mimetype)


def send_again(message_history_id):
    """
    send a message from message history again
    :param message_history_id The id of the message history to send again
    :return the sent message

    TO-DO : correction of send_message in osis-common to get the associated receiver , based on id and receiver model

    """
    message_history = message_history_mdl.find_by_id(message_history_id)
    person = person_mdl.find_by_id(message_history.receiver_id)
    if person:
        receiver = message_config.create_receiver(person.id, person.email, person.language)
        return message_service.send_again(receiver, message_history_id)
    else:
        return _('no_receiver_error')
