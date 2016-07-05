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
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from django.http.response import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from assistant.models import assistant_mandate, academic_assistant
from assistant.forms import AssistantDocumentForm


def user_is_assistant(user):
    """Use with a ``user_passes_test`` decorator to restrict access to 
    authenticated users who are assistant for the mandate_id."""
    try:
        if user.is_authenticated():
            return academic_assistant.AcademicAssistant.objects.get(person=user.person)
    except ObjectDoesNotExist:
        return False

@user_passes_test(user_is_assistant, login_url='assistants_home') 
def add_file(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    person = request.user.person
    assistant = mandate.assistant
    if person != assistant.person:
        return HttpResponseRedirect(reverse('assistant_mandates'))
    form = AssistantDocumentForm(request.POST, request.FILES, prefix='file')
    if form.is_valid():
        form.save()
    else:
        return render(request, "add_file.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'form': form}) 
    return HttpResponseRedirect(reverse('form_part3_edit', args=(mandate.id,)))
        