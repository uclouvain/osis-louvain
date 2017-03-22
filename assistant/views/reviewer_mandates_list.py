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
from assistant.models import reviewer, mandate_structure
from base.models import academic_year, structure
from assistant.forms import MandatesArchivesForm
from django.views.generic import ListView
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from assistant.models import settings, assistant_mandate


class MandatesListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'reviewer_mandates_list'
    template_name = 'reviewer_mandates_list.html'
    form_class = MandatesArchivesForm
    is_supervisor = False

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
        current_reviewer = reviewer.find_by_person(self.request.user.person)
        if len(assistant_mandate.find_for_supervisor_for_academic_year(self.request.user.person,
                                                                       academic_year.current_academic_year())) > 0:
            self.is_supervisor = True
        structures_id = structure.Structure.objects.filter(Q(id=current_reviewer.structure.id) |
                                                           Q(part_of_id=current_reviewer.structure.id)).\
            values_list('id', flat=True)
        mandates_id = mandate_structure.MandateStructure.objects.filter(structure__in=structures_id).\
            values_list('assistant_mandate_id', flat=True).distinct()
        if form.is_valid():
            self.request.session['selected_academic_year'] = form.cleaned_data[
                'academic_year'].id
            queryset = assistant_mandate.AssistantMandate.objects.filter(
                academic_year=form.cleaned_data['academic_year']).filter(id__in=mandates_id)
        elif self.request.session.get('selected_academic_year'):
            selected_academic_year = academic_year.AcademicYear.objects.get(
                id=self.request.session.get('selected_academic_year'))
            queryset = assistant_mandate.AssistantMandate.objects\
                .filter(academic_year=selected_academic_year).filter(id__in=mandates_id)
        else:
            selected_academic_year = academic_year.current_academic_year()
            self.request.session[
                'selected_academic_year'] = selected_academic_year.id
            queryset = assistant_mandate.find_by_academic_year(
                selected_academic_year).filter(id__in=mandates_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        phd_list = ['RESEARCH', 'SUPERVISION', 'VICE_RECTOR', 'DONE']
        research_list = ['SUPERVISION', 'VICE_RECTOR', 'DONE']
        supervision_list = ['VICE_RECTOR', 'DONE']
        vice_rector_list = ['VICE_RECTOR', 'DONE']
        current_reviewer = reviewer.find_by_person(self.request.user.person)
        can_delegate = reviewer.can_delegate(current_reviewer)
        context['can_delegate'] = can_delegate
        context['reviewer'] = current_reviewer
        context['phd_list'] = phd_list
        context['research_list'] = research_list
        context['supervision_list'] = supervision_list
        context['vice_rector_list'] = vice_rector_list
        context['is_supervisor'] = self.is_supervisor
        context['year'] = academic_year.find_academic_year_by_id(
            self.request.session.get('selected_academic_year')).year
        return context

    def get_initial(self):
        if self.request.session.get('selected_academic_year'):
            selected_academic_year = academic_year.find_academic_year_by_id(
                self.request.session.get('selected_academic_year'))
        else:
            selected_academic_year = academic_year.current_academic_year()
            self.request.session[
                'selected_academic_year'] = selected_academic_year.id
        return {'academic_year': selected_academic_year}
