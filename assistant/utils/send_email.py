##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
from osis_common.messaging import message_config, send_message as message_service
from base.models import academic_year
from assistant.models import assistant_mandate, settings, manager, reviewer
from django.shortcuts import redirect
from assistant.models.message import Message
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from assistant.enums import message_type
from assistant.utils import manager_access


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def send_message_to_assistants(request):
    mandates_for_current_academic_year = assistant_mandate.find_by_academic_year(
        academic_year.current_academic_year())
    for mandate in mandates_for_current_academic_year:
        if mandate.renewal_type == 'normal':
            html_template_ref = 'assistant_assistants_startup_normal_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_normal_renewal_txt'
        else:
            html_template_ref = 'assistant_assistants_startup_except_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_except_renewal_txt'
        send_message(mandate.assistant.person, html_template_ref, txt_template_ref)
    save_message_history(request, message_type.TO_ALL_ASSISTANTS)
    return redirect('messages_history')


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def send_message_to_deans(request):
    html_template_ref = 'assistant_deans_startup__html'
    txt_template_ref = 'assistant_deans_startup_txt'
    all_deans = reviewer.find_by_role('SUPERVISION')
    for dean in all_deans:
        send_message(dean.person, html_template_ref, txt_template_ref)
    save_message_history(request, message_type.TO_ALL_DEANS)
    return redirect('messages_history')


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def save_message_history(request, type):
    message = Message.objects.create(sender=manager.Manager.objects.get(person=request.user.person),
                                     date=timezone.now(),
                                     type=type,
                                     academic_year=academic_year.current_academic_year())
    message.save()


def send_message(person, html_template_ref, txt_template_ref, assistant=None):
    procedure_dates = settings.get_settings()
    receivers = [message_config.create_receiver(person.id, person.email,
                                                person.language)]
    first_ending_year = academic_year.current_academic_year().year + 1
    last_ending_year = first_ending_year + 1
    template_base_data = {'start_date': procedure_dates.starting_date, 'end_date': procedure_dates.ending_date,
                          'first_name': person.first_name, 'last_name': person.last_name,
                          'first_ending_year': first_ending_year,
                          'last_ending_year': last_ending_year}
    if assistant is not None:
        template_base_data['assistant'] = assistant.person
    subject_data = None
    table = None
    message_content = message_config.create_message_content(html_template_ref, txt_template_ref, table,
                                                            receivers, template_base_data, subject_data)
    return message_service.send_messages(message_content)
