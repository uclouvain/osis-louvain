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
from base.models import academic_year
from django.views.generic import ListView
from django.forms import forms
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from assistant.models import settings, assistant_mandate, reviewer


class AssistantsListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'phd_supervisor_assistants_list'
    template_name = 'phd_supervisor_assistants_list.html'
    form_class = forms.Form
    is_reviewer = False

    def test_func(self):
        if settings.access_to_procedure_is_open():
            try:
                return assistant_mandate.find_for_supervisor_for_academic_year(self.request.user.person,
                                                                               academic_year.current_academic_year())
            except ObjectDoesNotExist:
                return False

    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        try:
            reviewer.find_by_person(self.request.user.person)
            self.is_reviewer = True
        except ObjectDoesNotExist:
            self.is_reviewer = False
        return assistant_mandate.find_for_supervisor_for_academic_year(self.request.user.person,
                                                                       academic_year.current_academic_year())

    def get_context_data(self, **kwargs):
        context = super(AssistantsListView, self).get_context_data(**kwargs)
        context['year'] = academic_year.current_academic_year().year
        context['is_reviewer'] = self.is_reviewer
        if self.is_reviewer:
            can_delegate = reviewer.can_delegate(reviewer.find_by_person(self.request.user.person))
            context['can_delegate'] = can_delegate
        else:
            context['can_delegate'] = False
        return context
