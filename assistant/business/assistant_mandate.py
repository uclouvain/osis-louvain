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
from django.http.response import HttpResponseRedirect
from django.shortcuts import reverse
from django.views.decorators.http import require_http_methods

from assistant.models.assistant_mandate import find_mandate_by_id
from assistant.models.enums import assistant_mandate_state
from assistant.models.enums import assistant_type
from assistant.models.enums import review_status
from assistant.models.enums import reviewer_role
from assistant.models.review import find_done_by_supervisor_for_mandate
from assistant.models.review import get_in_progress_for_mandate
from assistant.models.review import find_review_for_mandate_by_role
from assistant.utils import manager_access


def mandate_can_go_backward(mandate):
    return not get_in_progress_for_mandate(mandate) and mandate.state != assistant_mandate_state.TO_DO


@require_http_methods(["POST"])
@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def find_assistant_mandate_step_backward_state(request):
    mandate_id = request.POST.get('mandate_id')
    mandate = find_mandate_by_id(mandate_id)
    if mandate.state == assistant_mandate_state.TRTS:
        make_assistant_mandate_step_backward(mandate=mandate, rev_role=None, state_to=assistant_mandate_state.TO_DO)
    elif mandate.state == assistant_mandate_state.PHD_SUPERVISOR:
        make_assistant_mandate_step_backward(mandate=mandate, rev_role=None, state_to=assistant_mandate_state.TRTS)
    elif mandate.state == assistant_mandate_state.RESEARCH:
        if mandate.assistant.supervisor:
            make_assistant_mandate_step_backward(mandate, reviewer_role.PHD_SUPERVISOR,
                                                 assistant_mandate_state.PHD_SUPERVISOR)
        else:
            make_assistant_mandate_step_backward(mandate=mandate, rev_role=None, state_to=assistant_mandate_state.TRTS)
    elif mandate.state == assistant_mandate_state.SUPERVISION:
        if mandate.assistant_type == assistant_type.ASSISTANT:
            make_assistant_mandate_step_backward(mandate=mandate, rev_role=reviewer_role.RESEARCH,
                                                 state_to=assistant_mandate_state.RESEARCH)
        else:
            make_assistant_mandate_step_backward(mandate=mandate, rev_role=None, state_to=assistant_mandate_state.TRTS)
    elif mandate.state == assistant_mandate_state.VICE_RECTOR:
        make_assistant_mandate_step_backward(mandate, reviewer_role.SUPERVISION, assistant_mandate_state.SUPERVISION)
    else:
        make_assistant_mandate_step_backward(mandate, reviewer_role.VICE_RECTOR, assistant_mandate_state.VICE_RECTOR)
    return HttpResponseRedirect(reverse('manager_reviews_view', kwargs={'mandate_id': mandate_id}))


def make_assistant_mandate_step_backward(mandate, rev_role, state_to):
    find_review_and_change_status(mandate, rev_role)
    mandate.state = state_to
    mandate.save()


def find_review_and_change_status(mandate, role):
    review = None
    if role == reviewer_role.PHD_SUPERVISOR:
        review = find_done_by_supervisor_for_mandate(mandate)
    elif role:
        review = find_review_for_mandate_by_role(mandate, role)
    if review:
        review.status = review_status.IN_PROGRESS
        review.save()


def add_actions_to_mandates_list(context, reviewer):
    cannot_view_assistant_form_status_list = [
        assistant_mandate_state.TO_DO,
        assistant_mandate_state.DECLINED,
        assistant_mandate_state.TRTS
    ]
    for mandate in context['object_list']:
        mandate.view = mandate.edit = False
        if mandate.state not in cannot_view_assistant_form_status_list:
            mandate.view = True
        if mandate.state in reviewer.role:
            mandate.edit = True
    return context
