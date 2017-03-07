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
from assistant.models import assistant_mandate, reviewer, mandate_structure
from base.models import academic_year, structure
from assistant.forms import MandatesArchivesForm
from django.views.generic import ListView
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from assistant.models import settings
from itertools import chain


class MandatesListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'reviewer_mandates_list'
    template_name = 'reviewer_mandates_list.html'
    form_class = MandatesArchivesForm
    is_only_supervisor_for_mandates = []
    is_reviewer_for_mandates = []

    def test_func(self):
        if settings.access_to_procedure_is_open():
            try:
                return reviewer.find_by_person(self.request.user.person)
            except ObjectDoesNotExist:
                return False

    def get_login_url(self):
        return reverse('access_denied')


    def get_queryset(self):
        form_class = MandatesArchivesForm
        form = form_class(self.request.GET)
        current_reviewer =  reviewer.find_by_person(self.request.user.person)
        current_reviewer_mandates = []
        mandates_structures = []
        if form.is_valid():
            self.request.session['selected_academic_year'] = form.cleaned_data[
                'academic_year'].id
        else:
            self.request.session['selected_academic_year'] = academic_year.current_academic_year().id
        if current_reviewer.is_phd_supervisor:
            current_reviewer_mandates.extend\
                (assistant_mandate.find_for_supervisor_for_academic_year(
                    current_reviewer, self.request.session['selected_academic_year']))
        for mandate in current_reviewer_mandates:
            self.is_only_supervisor_for_mandates.append(mandate.id)
        if current_reviewer.structure:
            all_structures_for_current_reviewer = []
            for structure in current_reviewer.structure.children:
                all_structures_for_current_reviewer.append(structure)
            all_structures_for_current_reviewer.append(current_reviewer.structure)
            mandates_structures.extend(mandate_structure.find_by_structures_for_academic_year(
                all_structures_for_current_reviewer, self.request.session['selected_academic_year']))
            for mandate_struct in mandates_structures:
                self.is_reviewer_for_mandates.append(mandate_struct.assistant_mandate.id)
                if mandate_struct.assistant_mandate not in current_reviewer_mandates:
                    current_reviewer_mandates.append(mandate_struct.assistant_mandate)
        self.is_only_supervisor_for_mandates = list(set(self.is_only_supervisor_for_mandates) - \
                                               set(self.is_reviewer_for_mandates))
        return current_reviewer_mandates

    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        phd_list = ['RESEARCH', 'SUPERVISION', 'VICE_RECTOR', 'DONE']
        research_list = ['SUPERVISION', 'VICE_RECTOR', 'DONE']
        supervision_list = ['VICE_RECTOR', 'DONE']
        vice_rector_list = ['VICE_RECTOR', 'DONE']
        current_reviewer = reviewer.find_by_person(self.request.user.person)
        can_delegate = reviewer.can_delegate(current_reviewer)
        context['can_delegate']= can_delegate
        context['reviewer'] = current_reviewer
        context['phd_list'] = phd_list
        context['research_list'] = research_list
        context['supervision_list'] = supervision_list
        context['vice_rector_list'] = vice_rector_list
        context['is_only_supervisor_for_mandates'] = self.is_only_supervisor_for_mandates
        context['year'] = academic_year.find_academic_year_by_id(
            self.request.session.get('selected_academic_year')).year
        return context

    def get_initial(self):
        if 'selected_academic_year' not in self.request.session:
            self.request.session['selected_academic_year'] = academic_year.current_academic_year()
        return {'academic_year': self.request.session['selected_academic_year']}
