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
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from assistant.models import review, academic_assistant, settings, assistant_mandate


def user_is_assistant_and_procedure_is_open(user):
    try:
        if user.is_authenticated() and settings.access_to_procedure_is_open():
            return academic_assistant.find_by_person(user.person)
        else:
            return False
    except ObjectDoesNotExist:
        return False


@user_passes_test(user_is_assistant_and_procedure_is_open, login_url='access_denied')
def reviews_view(request, mandate_id):
    reviews = review.find_by_mandate(mandate_id)
    current_academic_assistant = academic_assistant.find_by_person(request.user.person)
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    if mandate.assistant != current_academic_assistant:
        return HttpResponseRedirect(reverse("assistants_home"))
    else:
        return render(request, 'mandate_reviews_view.html', {'reviews': reviews})
