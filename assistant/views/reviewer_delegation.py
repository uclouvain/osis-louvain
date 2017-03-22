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
from django.shortcuts import render, redirect
from assistant.models import reviewer
from base.models import academic_year, structure, person
from assistant.forms import ReviewerDelegationForm
from django.views.generic import ListView
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import user_passes_test
from assistant.models import settings
from django.utils.translation import ugettext as _
from assistant.models import assistant_mandate
from assistant.enums import reviewer_role


class StructuresListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'reviewer_structures_list'
    template_name = 'reviewer_structures_list.html'
    form_class = ReviewerDelegationForm
    is_supervisor = False

    def test_func(self):
        try:
            if settings.access_to_procedure_is_open():
                return reviewer.can_delegate(reviewer.find_by_person(self.request.user.person))
        except ObjectDoesNotExist:
            return False
    
    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        if len(assistant_mandate.find_for_supervisor_for_academic_year(self.request.user.person,
                                                                       academic_year.current_academic_year())) > 0:
            self.is_supervisor = True
        rev = reviewer.find_by_person(self.request.user.person)
        queryset = structure.Structure.objects.filter(Q(id=rev.structure.id) | Q(part_of_id=rev.structure.id))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(StructuresListView, self).get_context_data(**kwargs)
        context['year'] = academic_year.current_academic_year().year
        context['current_reviewer'] = reviewer.find_by_person(self.request.user.person)
        context['is_supervisor'] = self.is_supervisor
        return context


def user_is_reviewer_and_can_delegate(user):
    """Use with a ``user_passes_test`` decorator to restrict access to
    authenticated users who are reviewer and can delegate."""

    try:
        if user.is_authenticated() and settings.access_to_procedure_is_open():
            return reviewer.Reviewer.objects.get(Q(person=user.person) &
                                                   (Q(role=reviewer_role.SUPERVISION) | Q(role=reviewer_role.RESEARCH)))
    except ObjectDoesNotExist:
        return False


@user_passes_test(user_is_reviewer_and_can_delegate, login_url='assistants_home')
def add_reviewer_for_structure(request, structure_id):
    """
    Crée un reviewer pour une structure donnée.
    structure_id est l'identifiant de la structure pour laquelle on ajoute un reviewer.
    Si le rôle du reviewer créé dépend du rôle de l'utilisateur (reviewer) connecté.
    """
    related_structure = structure.find_by_id(structure_id)
    year = academic_year.current_academic_year().year
    try:
        reviewer.can_delegate_to_structure(reviewer.find_by_person(request.user.person), related_structure)
    except:
        return redirect('assistants_home')
    if request.POST:
        form = ReviewerDelegationForm(data=request.POST)
        if form.is_valid():
            new_reviewer = form.save(commit=False)
            if request.POST.get('person_id'):
                this_person = person.find_by_id(request.POST.get('person_id'))
                try:
                    reviewer.find_by_person(this_person)
                    msg = _("person_already_reviewer_msg")
                    form.add_error(None, msg)
                    return render(request, "reviewer_add_reviewer.html", {'form': form, 'year': year,
                                                                          'related_structure': related_structure})
                except reviewer.Reviewer.DoesNotExist:
                    pass
                new_reviewer.person = this_person
                new_reviewer.save()
                return redirect('reviewer_delegation')
        else:
            return render(request, "reviewer_add_reviewer.html", {'form': form, 'year': year,
                                                                  'related_structure': related_structure})
    else:
        this_reviewer = reviewer.find_by_person(person=request.user.person)
        if this_reviewer.role == reviewer_role.SUPERVISION:
            role = reviewer_role.SUPERVISION_ASSISTANT
        else: 
            role = reviewer_role.RESEARCH_ASSISTANT
        form = ReviewerDelegationForm(initial={'structure': related_structure, 'year': year, 'role': role})
        return render(request, "reviewer_add_reviewer.html", {'form': form, 'year': year,
                                                              'related_structure': related_structure})
