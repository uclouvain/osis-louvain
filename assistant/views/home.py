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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from assistant.models import academic_assistant, manager, reviewer
from assistant.models import settings
from assistant.utils import manager_access


@login_required
def assistant_home(request):
    try:
        academic_assistant.find_by_person(person=request.user.person)
        if settings.access_to_procedure_is_open():
            return HttpResponseRedirect(reverse('assistant_mandates'))
        else:
            return HttpResponseRedirect(reverse('access_denied'))
    except academic_assistant.AcademicAssistant.DoesNotExist:
        try:
            manager.find_by_person(person=request.user.person)
            return HttpResponseRedirect(reverse('manager_home'))
        except manager.Manager.DoesNotExist:
            try:
                reviewer.find_by_person(person=request.user.person)
                return HttpResponseRedirect(reverse('reviewer_mandates_list'))
            except reviewer.Reviewer.DoesNotExist:
                return HttpResponseRedirect(reverse('access_denied'))


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def manager_home(request):
    return render(request, 'manager_home.html')


def access_denied(request):
    return render(request, "access_denied.html")
