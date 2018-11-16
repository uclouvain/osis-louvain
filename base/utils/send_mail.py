##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django.contrib.auth.models import Permission
from django.contrib.messages import ERROR
from django.db.models import Q
from django.utils.translation import ugettext as _
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from assessments.business import score_encoding_sheet
from base.models import person as person_mdl
from base.models.academic_year import current_academic_year
from base.models.person import Person
from osis_common.document import paper_sheet, xls_build
from osis_common.document.xls_build import _adjust_column_width
from osis_common.messaging import message_config, send_message as message_service
from osis_common.models import message_history as message_history_mdl

EDUCATIONAL_INFORMATION_UPDATE_TXT = 'educational_information_update_txt'

EDUCATIONAL_INFORMATION_UPDATE_HTML = 'educational_information_update_html'


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
                          'encoding_status': _('All the scores are encoded.') if all_encoded
                          else _('It remains notes to encode.')
                          }
    header_txt = ['acronym', 'session_title', 'registration_number', 'lastname', 'firstname', 'score', 'documentation']
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


def send_mail_after_the_learning_unit_year_deletion(managers, acronym, academic_year, msg_list):
    html_template_ref = 'learning_unit_year_deletion_html'
    txt_template_ref = 'learning_unit_year_deletion_txt'
    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language) for manager in managers]
    suject_data = {'learning_unit_acronym': acronym}
    template_base_data = {'learning_unit_acronym': acronym,
                          'academic_year': academic_year,
                          'msg_list': msg_list,
                          }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, suject_data, None)
    return message_service.send_messages(message_content)


def send_mail_before_annual_procedure_of_automatic_postponement_of_luy(
        end_academic_year, luys_to_postpone, luys_already_existing, luys_ending_this_year):
    html_template_ref = 'luy_before_auto_postponement_html'
    txt_template_ref = 'luy_before_auto_postponement_txt'

    permission = Permission.objects.filter(codename='can_receive_emails_about_automatic_postponement')
    managers = Person.objects.filter(Q(user__groups__permissions=permission) | Q(user__user_permissions=permission)) \
        .distinct()

    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language) for manager in managers]
    template_base_data = {'academic_year': current_academic_year().year,
                          'end_academic_year': end_academic_year.year,
                          'luys_to_postpone': luys_to_postpone.count(),
                          'luys_already_existing': luys_already_existing.count(),
                          'luys_ending_this_year': luys_ending_this_year.count(),
                          }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, None, None)
    return message_service.send_messages(message_content)


def send_mail_after_annual_procedure_of_automatic_postponement_of_luy(
        end_academic_year, luys_postponed, luys_already_existing, luys_ending_this_year, luys_with_errors):
    html_template_ref = 'luy_after_auto_postponement_html'
    txt_template_ref = 'luy_after_auto_postponement_txt'

    permission = Permission.objects.filter(codename='can_receive_emails_about_automatic_postponement')
    managers = Person.objects.filter(Q(user__groups__permissions=permission) | Q(user__user_permissions=permission)) \
        .distinct()

    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language) for manager in managers]
    template_base_data = {'academic_year': current_academic_year().year,
                          'end_academic_year': end_academic_year.year,
                          'luys_postponed': len(luys_postponed),
                          'luys_already_existing': luys_already_existing.count(),
                          'luys_ending_this_year': luys_ending_this_year.count(),
                          'luys_with_errors': luys_with_errors
                          }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, None, None)
    return message_service.send_messages(message_content)


def send_mail_before_annual_procedure_of_automatic_postponement_of_egy(
        end_academic_year, egys_to_postpone, egys_already_existing, egys_ending_this_year):
    html_template_ref = 'egy_before_auto_postponement_html'
    txt_template_ref = 'egy_before_auto_postponement_txt'

    permission = Permission.objects.filter(codename='can_receive_emails_about_automatic_postponement')
    managers = Person.objects.filter(Q(user__groups__permissions=permission) | Q(user__user_permissions=permission)) \
        .distinct()

    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language) for manager in managers]
    template_base_data = {'academic_year': current_academic_year().year,
                          'end_academic_year': end_academic_year.year,
                          'egys_to_postpone': egys_to_postpone.count(),
                          'egys_already_existing': egys_already_existing.count(),
                          'egys_ending_this_year': egys_ending_this_year.count(),
                          }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, None, None)
    return message_service.send_messages(message_content)


def send_mail_after_annual_procedure_of_automatic_postponement_of_egy(
        end_academic_year, egys_postponed, egys_already_existing, egys_ending_this_year, egys_with_errors):
    html_template_ref = 'egy_after_auto_postponement_html'
    txt_template_ref = 'egy_after_auto_postponement_txt'

    permission = Permission.objects.filter(codename='can_receive_emails_about_automatic_postponement')
    managers = Person.objects.filter(Q(user__groups__permissions=permission) | Q(user__user_permissions=permission)) \
        .distinct()

    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language) for manager in managers]
    template_base_data = {'academic_year': current_academic_year().year,
                          'end_academic_year': end_academic_year.year,
                          'egys_postponed': len(egys_postponed),
                          'egys_already_existing': egys_already_existing.count(),
                          'egys_ending_this_year': egys_ending_this_year.count(),
                          'egys_with_errors': egys_with_errors
                          }
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, None, None)
    return message_service.send_messages(message_content)


def send_mail_cancellation_learning_unit_proposals(manager, tuple_proposals_results, research_criteria):
    html_template_ref = 'learning_unit_proposal_canceled_html'
    txt_template_ref = 'learning_unit_proposal_canceled_txt'
    return _send_mail_action_learning_unit_proposal(manager, tuple_proposals_results, html_template_ref,
                                                    txt_template_ref, "cancellation", research_criteria)


def send_mail_consolidation_learning_unit_proposal(manager, tuple_proposals_results, research_criteria):
    html_template_ref = 'learning_unit_proposal_consolidated_html'
    txt_template_ref = 'learning_unit_proposal_consolidated_txt'
    return _send_mail_action_learning_unit_proposal(manager, tuple_proposals_results, html_template_ref,
                                                    txt_template_ref, "consolidation", research_criteria)


def _send_mail_action_learning_unit_proposal(manager, tuple_proposals_results, html_template_ref, txt_template_ref,
                                             operation, research_criteria):
    receivers = [message_config.create_receiver(manager.id, manager.email, manager.language)]
    suject_data = {}
    template_base_data = {
        "first_name": manager.first_name,
        "last_name": manager.last_name
    }
    attachment = ("report.xlsx",
                  build_proposal_report_attachment(manager, tuple_proposals_results, operation, research_criteria),
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, suject_data, attachment=attachment)
    return message_service.send_messages(message_content)


# FIXME should be moved to osis_common
def build_proposal_report_attachment(manager, proposals_with_results, operation, research_criteria):
    table_data = _build_table_proposal_data(proposals_with_results)

    xls_parameters = {
        xls_build.LIST_DESCRIPTION_KEY: "Liste d'activités",
        xls_build.FILENAME_KEY: 'Learning_units',
        xls_build.USER_KEY: str(manager),
        xls_build.WORKSHEETS_DATA: [
            {
                xls_build.CONTENT_KEY: table_data,
                xls_build.HEADER_TITLES_KEY: [_('Ac yr.'), _('code'), _('Title'), _('type'),
                                              _("Proposal status"), _('Status'), _('Remarks')],
                xls_build.WORKSHEET_TITLE_KEY: 'Report'
            }
        ],
        "operation": operation,
        "research_criteria": research_criteria
    }

    return _create_xls(xls_parameters)


def _build_table_proposal_data(proposals_with_results):
    return [
        (
            proposal.learning_unit_year.academic_year.name,
            proposal.learning_unit_year.acronym,
            proposal.learning_unit_year.complete_title,
            _(proposal.type),
            _(proposal.state),
            _("Success") if ERROR not in results else _("Failure"),
            "\n".join(results.get(ERROR, []))
        ) for (proposal, results) in proposals_with_results
    ]


# FIXME should be moved to osis_common
def _create_xls(parameters_dict):
    workbook = Workbook(encoding='utf-8')
    sheet_number = 0
    for worksheet_data in parameters_dict.get(xls_build.WORKSHEETS_DATA):
        xls_build._build_worksheet(worksheet_data, workbook, sheet_number)
        sheet_number = sheet_number + 1

    _build_worksheet_parameters(workbook, parameters_dict.get(xls_build.USER_KEY),
                                parameters_dict.get("operation", ""), parameters_dict.get("research_criteria"))
    return save_virtual_workbook(workbook)


# FIXME should be moved to osis_common
def _build_worksheet_parameters(workbook, a_user, operation, research_criteria):
    worksheet_parameters = workbook.create_sheet(title=str(_('parameters')))
    now = datetime.datetime.now()
    worksheet_parameters.append([str(_('author')), str(a_user)])
    worksheet_parameters.append([str(_('Date')), now.strftime('%d-%m-%Y %H:%M')])
    worksheet_parameters.append([_('Operation'), _(operation)])
    if research_criteria:
        worksheet_parameters.append([_('Research criteria')])
        for research_key, research_value in research_criteria:
            worksheet_parameters.append(["", research_key, str(research_value)])

    _adjust_column_width(worksheet_parameters)
    return worksheet_parameters


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
        'offer_acronym': offer_acronym
    }
    template_base_data = {
        'learning_unit_acronym': learning_unit_acronym,
        'offer_acronym': offer_acronym,
    }
    enrollments_data = [
        (
            enrollment.learning_unit_enrollment.offer_enrollment.offer_year.acronym,
            enrollment.session_exam.number_session,
            enrollment.learning_unit_enrollment.offer_enrollment.student.registration_id,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.last_name,
            enrollment.learning_unit_enrollment.offer_enrollment.student.person.first_name,
            enrollment.score_final,
            enrollment.justification_final if enrollment.justification_final else None,
        ) for enrollment in enrollments]
    enrollments_headers = (
        'acronym',
        'session_title',
        'registration_number',
        'lastname',
        'firstname',
        'score',
        'justification'
    )
    table = message_config.create_table('enrollments', enrollments_headers, enrollments_data,
                                        data_translatable=['justification'])
    attachment = build_scores_sheet_attachment(enrollments)
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref,
                                                            [table], receivers, template_base_data, suject_data,
                                                            attachment)
    return message_service.send_messages(message_content)


def build_scores_sheet_attachment(list_exam_enrollments):
    name = "%s.pdf" % _('score(s) saved')
    mimetype = "application/pdf"
    content = paper_sheet.build_pdf(
        score_encoding_sheet.scores_sheet_data(list_exam_enrollments, tutor=None))
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
        return _('No receiver for this message')


def send_mail_for_educational_information_update(teachers, learning_units_years):
    html_template_ref = EDUCATIONAL_INFORMATION_UPDATE_HTML
    txt_template_ref = EDUCATIONAL_INFORMATION_UPDATE_TXT
    receivers = [message_config.create_receiver(teacher.id, teacher.email, teacher.language) for teacher in teachers]
    template_base_data = {'learning_unit_years': learning_units_years}

    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, None, receivers,
                                                            template_base_data, {}, None)
    return message_service.send_messages(message_content)
