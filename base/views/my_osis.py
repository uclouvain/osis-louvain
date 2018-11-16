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
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext as _

import base.business.learning_unit
from base import models as mdl
from attribution import models as mdl_attr
from base.forms.my_message import MyMessageActionForm, MyMessageForm
from base.utils import send_mail
from base.views import layout
from osis_common.models import message_history as message_history_mdl
from django.shortcuts import redirect


@login_required
def my_osis_index(request):
    return layout.render(request, "my_osis/home.html", {})


@login_required
def my_messages_index(request):
    person = mdl.person.find_by_user(request.user)
    my_messages = message_history_mdl.find_my_messages(person.id)
    my_messages_formset = None
    if not my_messages:
        messages.add_message(request, messages.INFO, _('No Messages'))
    else:
        my_messages_formset = get_messages_formset(my_messages)
    return layout.render(request,
                         "my_osis/my_messages.html",
                         {
                             'my_messages_formset': my_messages_formset,
                             'my_message_action_form': MyMessageActionForm()
                         })


@login_required
def my_messages_action(request):
    my_message_action_form = MyMessageActionForm(request.POST)
    my_messages_formset = formset_factory(MyMessageForm)(request.POST, request.FILES)
    if my_message_action_form.is_valid() and my_messages_formset.is_valid():
        my_messages_ids_to_action = [mess_form.cleaned_data.get('id')
                                     for mess_form in my_messages_formset
                                     if mess_form.cleaned_data.get('selected')]
        if 'MARK_AS_READ' in my_message_action_form.cleaned_data.get('action'):
            message_history_mdl.mark_as_read(my_messages_ids_to_action)
        elif 'DELETE' in my_message_action_form.cleaned_data.get('action'):
            message_history_mdl.delete_my_messages(my_messages_ids_to_action)
    return HttpResponseRedirect(reverse('my_messages'))


@login_required
def delete_from_my_messages(request, message_id):
    message = message_history_mdl.find_by_id(message_id)
    person_user = mdl.person.find_by_user(request.user)
    if message and (message.receiver_id == person_user.id):
        message_history_mdl.delete_my_messages([message_id, ])
    return HttpResponseRedirect(reverse('my_messages'))


@login_required
def read_message(request, message_id):
    message = message_history_mdl.read_my_message(message_id)
    return layout.render(request, "my_osis/my_message.html", {'my_message': message, })


@login_required
def profile(request):
    return layout.render(request, "my_osis/profile.html", _get_data(request))


@login_required
def profile_lang(request):
    ui_language = request.POST.get('ui_language')
    mdl.person.change_language(request.user, ui_language)
    translation.activate(ui_language)
    request.session[translation.LANGUAGE_SESSION_KEY] = ui_language
    return profile(request)


@login_required
def profile_lang_edit(request, ui_language):
    mdl.person.change_language(request.user, ui_language)
    translation.activate(ui_language)
    request.session[translation.LANGUAGE_SESSION_KEY] = ui_language
    return redirect(request.META['HTTP_REFERER'])


@login_required
@user_passes_test(lambda u: u.is_staff and u.has_perm('osis_common.change_messagetemplate'))
def messages_templates_index(request):
    return HttpResponseRedirect(reverse('admin:base_messagetemplate_changelist'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def send_message_again(request, message_id):
    message_history = message_history_mdl.find_by_id(message_id)

    if not has_email(message_history):
        messages.add_message(request, messages.ERROR, _("The message can't be sent again, no email provided."))
    else:
        send_mail.send_again(message_id)
        messages.add_message(request, messages.INFO, _('The message was sent again.'))
    return HttpResponseRedirect(reverse('admin:base_messagehistory_changelist'))


@login_required
def profile_attributions(request):
    data = _get_data(request)
    data.update({'tab_attribution_on': True})
    return layout.render(request, "my_osis/profile.html", data)


@login_required
def _get_data(request):
    person = mdl.person.find_by_user(request.user)
    tutor = mdl.tutor.find_by_person(person)
    return {'person': person,
            'addresses': mdl.person_address.find_by_person(person),
            'tutor': tutor,
            'attributions': mdl_attr.attribution.search(tutor=tutor),
            'programs_managers': mdl.program_manager.find_by_person(person),
            'supported_languages': settings.LANGUAGES,
            'default_language': settings.LANGUAGE_CODE,
            'summary_submission_opened': base.business.learning_unit.is_summary_submission_opened()}


def get_messages_formset(my_messages):
    initial_formset_content = [{'selected': False,
                                'subject': message_hist.subject,
                                'created': message_hist.created,
                                'id': message_hist.id,
                                'read': message_hist.read_by_user
                                } for message_hist in my_messages]
    return formset_factory(MyMessageForm, extra=0)(initial=initial_formset_content)


def has_email(message_history):
    person = mdl.person.find_by_id(message_history.receiver_id)
    if person and person.email:
        return True
    return False
