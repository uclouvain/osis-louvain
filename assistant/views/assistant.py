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
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods
from django.forms import forms

import base.models.entity
from base.models.academic_year import current_academic_year
from base.models import person, academic_year
from base.models.enums import entity_type
from assistant.models import academic_assistant, assistant_mandate, assistant_document_file
from django.views.generic.list import ListView
from django.views.generic.edit import FormMixin
from django.http.response import HttpResponseRedirect
from assistant.models import tutoring_learning_unit_year
from assistant.models import settings, reviewer, mandate_entity
from assistant.models.enums import document_type, assistant_mandate_state, reviewer_role
from assistant.utils.send_email import send_message
from assistant.utils import assistant_access


class AssistantMandatesListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):

    context_object_name = 'assistant_mandates_list'
    template_name = 'assistant_mandates.html'
    form_class = forms.Form

    def test_func(self):
        return assistant_access.user_is_assistant_and_procedure_is_open(self.request.user)

    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        assistant = academic_assistant.find_by_person(person.find_by_user(self.request.user))
        return assistant_mandate.find_mandate_by_academic_assistant(assistant)

    def get_context_data(self, **kwargs):
        context = super(AssistantMandatesListView, self).get_context_data(**kwargs)
        context['assistant'] = academic_assistant.find_by_person(person.find_by_user(self.request.user))
        context['current_academic_year'] = current_academic_year()
        context['can_see_file'] = settings.assistants_can_see_file()
        for mandate in context['object_list']:
            entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
            mandate.entities = base.models.entity.find_versions_from_entites(entities_id,
                                                                             mandate.academic_year.start_date)
        return context


@user_passes_test(assistant_access.user_is_assistant_and_procedure_is_open, login_url='access_denied')
@require_http_methods(["POST"])
def mandate_change_state(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        if 'bt_mandate_accept' in request.POST:
            mandate.state = assistant_mandate_state.TRTS
        elif 'bt_mandate_decline' in request.POST:
            mandate.state = assistant_mandate_state.DECLINED
            faculty = mandate_entity.find_by_mandate_and_type(mandate, entity_type.FACULTY)
            if faculty:
                faculty_dean = reviewer.find_by_entity_and_role(
                    faculty.first().entity, reviewer_role.SUPERVISION).first()
                pers = person.find_by_user(request.user)
                assistant = academic_assistant.find_by_person(pers)
                html_template_ref = 'assistant_dean_assistant_decline_html'
                txt_template_ref = 'assistant_dean_assistant_decline_txt'
                send_message(person=faculty_dean.person, html_template_ref=html_template_ref,
                             txt_template_ref=txt_template_ref, assistant=assistant)
        mandate.save()
    return HttpResponseRedirect(reverse('assistant_mandates'))


class AssistantLearningUnitsListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'mandate_learning_units_list'
    template_name = 'mandate_learning_unit_list.html'
    form_class = forms.Form

    def test_func(self):
        return assistant_access.user_is_assistant_and_procedure_is_open_and_workflow_is_assistant(self.request.user)

    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
            academic_assistant.find_by_person(self.request.user.person), academic_year.current_academic_year())
        queryset = tutoring_learning_unit_year.find_by_mandate(mandate)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AssistantLearningUnitsListView, self).get_context_data(**kwargs)
        mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
            academic_assistant.find_by_person(self.request.user.person), academic_year.current_academic_year())
        context['mandate_id'] = mandate.id
        context['assistant_type'] = mandate.assistant_type
        files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                  document_type.TUTORING_DOCUMENT)
        context['files'] = files
        context['document_type'] = document_type.TUTORING_DOCUMENT
        return context
