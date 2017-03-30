##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.utils.send_mail import *
from dissertation.models.dissertation_role import get_promoteur_by_dissertation


def get_template_de_base(dissert):
    template_base_data = {'author': dissert.author.person.last_name + ' ' + dissert.author.person.first_name
                                    + ' ' + dissert.author.person.global_id,
                          'title': dissert.title,
                          'promoteur': get_promoteur_by_dissertation(dissert).person.last_name
                                       + ' ' + get_promoteur_by_dissertation(dissert).person.first_name,
                          'description': dissert.description,
                          'dissertation_proposition_titre': dissert.proposition_dissertation.title}
    return template_base_data


def send_mail_to_teacher_new_dissert(dissert):
    html_template_ref = 'dissertation_adviser_new_project_dissertation_html'
    txt_template_ref = 'dissertation_adviser_new_project_dissertation_txt'
    teacher_promoteur = get_promoteur_by_dissertation(dissert)
    receivers = [message_config.create_receiver(teacher_promoteur.person.id,
                                                teacher_promoteur.person.email,
                                                teacher_promoteur.person.language)]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_accepted_by_teacher(dissert):
    html_template_ref = 'dissertation_accepted_by_teacher_html'
    txt_template_ref = 'dissertation_accepted_by_teacher_txt'
    receivers = [message_config.create_receiver(dissert.author.person.id,
                                                dissert.author.person.email,
                                                dissert.author.person.language)]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_refused_by_teacher(dissert):
    html_template_ref = 'dissertation_refused_by_teacher_html'
    txt_template_ref = 'dissertation_refused_by_teacher_txt'
    receivers = [message_config.create_receiver(dissert.author.person.id,
                                                dissert.author.person.email,
                                                dissert.author.person.language)]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_acknowledgement(dissert):
    html_template_ref = 'dissertation_acknowledgement_html'
    txt_template_ref = 'dissertation_acknowledgement_txt'
    receivers = [message_config.create_receiver(dissert.author.person.id,
                                                dissert.author.person.email,
                                                dissert.author.person.language)]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_refused_by_com_to_student(dissert):
    html_template_ref = 'dissertation_refused_by_com_to_student_html'
    txt_template_ref = 'dissertation_refused_by_com_to_student_txt'
    student_receiver = message_config.create_receiver(dissert.author.person.id,
                                                      dissert.author.person.email,
                                                      dissert.author.person.language)
    receivers = [student_receiver]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_refused_by_com_to_teacher(dissert):
    html_template_ref = 'dissertation_refused_by_com_to_teacher_html'
    txt_template_ref = 'dissertation_refused_by_com_to_teacher_txt'
    teacher_promoteur = get_promoteur_by_dissertation(dissert)
    teachers_receiver = message_config.create_receiver(teacher_promoteur.person.id,
                                                       teacher_promoteur.person.email,
                                                       teacher_promoteur.person.language)
    receivers = [teachers_receiver]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref,
                                                            txt_template_ref,
                                                            tables,
                                                            receivers,
                                                            template_base_data,
                                                            suject_data)
    return message_service.send_messages(message_content)


def send_mail_dissert_accepted_by_com(dissert):
    html_template_ref = 'dissertation_accepted_by_com_html'
    txt_template_ref = 'dissertation_accepted_by_com_txt'
    receivers = [message_config.create_receiver(dissert.author.person.id,
                                                dissert.author.person.email,
                                                dissert.author.person.language)]
    suject_data = None
    template_base_data = get_template_de_base(dissert)
    tables = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, tables, receivers,
                                                            template_base_data, suject_data)
    return message_service.send_messages(message_content)
