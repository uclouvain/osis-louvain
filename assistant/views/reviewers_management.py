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
from assistant.models import manager, reviewer
from django.core.urlresolvers import reverse
from assistant.forms import MandatesArchivesForm, ReviewerForm
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from base.models import academic_year, person
from django.utils.translation import ugettext as _
from assistant.utils import manager_access


class ReviewersListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'reviewers_list'
    template_name = 'reviewers_list.html'
    form_class = MandatesArchivesForm

    def test_func(self):
        return manager_access.user_is_manager(self.request.user)

    def get_login_url(self):
        return reverse('assistants_home')

    def get_queryset(self):
        queryset = reviewer.find_reviewers()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ReviewersListView, self).get_context_data(**kwargs)
        return context


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_delete(request, reviewer_id):
    reviewer_to_delete = reviewer.find_by_id(reviewer_id)
    reviewer_to_delete.delete()
    return redirect('reviewers_list')


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def reviewer_add(request):
    year = academic_year.current_academic_year().year
    if request.POST:
        form = ReviewerForm(data=request.POST)
        if form.is_valid():
            new_reviewer = form.save(commit=False)
            if request.POST.get('person_id'):
                this_person = person.find_by_id(request.POST.get('person_id'))
                try:
                    reviewer.find_by_person(this_person)
                    msg = _("person_already_reviewer_msg")
                    form.add_error(None, msg)
                    return render(request, "manager_add_reviewer.html", {'form': form, 'year': year})
                except reviewer.Reviewer.DoesNotExist:
                    pass
                new_reviewer.person = this_person
                new_reviewer.save()
                return redirect('reviewers_list')
        else:
            return render(request, "manager_add_reviewer.html", {'form': form, 'year': year})
    else:
        form = ReviewerForm(initial={'year': year})
        return render(request, "manager_add_reviewer.html", {'form': form, 'year': year})
