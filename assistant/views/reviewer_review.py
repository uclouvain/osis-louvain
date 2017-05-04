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
from django.http.response import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from assistant.models import assistant_mandate, review, mandate_structure, tutoring_learning_unit_year
from assistant.models import reviewer
from base.models import person
from assistant.forms import ReviewForm
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from assistant.enums import reviewer_role
from base.enums import structure_type
from assistant.models.enums import review_status, assistant_mandate_state
import re



@login_required
def review_view(request, mandate_id, role):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = reviewer.find_by_person(request.user.person)
    current_role = current_reviewer.role
    if role == reviewer_role.PHD_SUPERVISOR:
        try:
            current_review = review.find_done_by_supervisor_for_mandate(mandate)
        except ObjectDoesNotExist:
            current_review = None
    else:
        current_review = review.find_review_for_mandate_by_role(mandate, role)
    assistant = mandate.assistant
    menu = generate_reviewer_menu_tabs(current_role, mandate, role)
    return render(request, 'review_view.html', {'review': current_review,
                                                'role': current_role,
                                                'menu': menu,
                                                'menu_type': 'reviewer_menu',
                                                'mandate_id': mandate.id,
                                                'mandate_state': mandate.state,
                                                'assistant': assistant,
                                                'year': mandate.academic_year.year + 1
                                                })


@login_required
def review_edit(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = reviewer.can_edit_review(reviewer.find_by_person(person.find_by_user(request.user)).id, mandate_id)
    delegate_role = current_reviewer.role + "_ASSISTANT"
    existing_review = review.find_review_for_mandate_by_role(mandate, delegate_role)
    if existing_review is None:
        existing_review, created = review.Review.objects.get_or_create(
            mandate=mandate,
            reviewer=current_reviewer,
            status=review_status.IN_PROGRESS
        )
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    role = current_reviewer.role
    menu = generate_reviewer_menu_tabs(role, mandate, role)
    assistant = mandate.assistant
    form = ReviewForm(initial={'mandate': mandate,
                               'reviewer': existing_review.reviewer,
                               'status': existing_review.status,
                               'advice': existing_review.advice,
                               'changed': timezone.now,
                               'confidential': existing_review.confidential,
                               'remark': existing_review.remark
                               }, prefix="rev", instance=existing_review)
    return render(request, 'review_form.html', {'review': existing_review,
                                                'role': role,
                                                'year': mandate.academic_year.year + 1,
                                                'absences': mandate.absences,
                                                'comment': mandate.comment,
                                                'mandate_id': mandate.id,
                                                'previous_mandates': previous_mandates,
                                                'assistant': assistant,
                                                'menu': menu,
                                                'menu_type': 'reviewer_menu',
                                                'form': form})


@login_required
def review_save(request, review_id, mandate_id):
    rev = review.find_by_id(review_id)
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    form = ReviewForm(data=request.POST, instance=rev, prefix='rev')
    if form.is_valid():
        current_review = form.save(commit=False)
        if 'validate_and_submit' in request.POST:
            current_review.status = review_status.DONE
            current_review.save()
            if mandate.state == assistant_mandate_state.PHD_SUPERVISOR:
                if mandate_structure.find_by_mandate_and_type(mandate, 'INSTITUTE'):
                    mandate.state = assistant_mandate_state.RESEARCH
                elif mandate_structure.find_by_mandate_and_part_of_type(mandate, 'INSTITUTE'):
                    mandate.state = assistant_mandate_state.RESEARCH
                else:
                    mandate.state = assistant_mandate_state.SUPERVISION
            elif mandate.state == assistant_mandate_state.RESEARCH:
                mandate.state = assistant_mandate_state.SUPERVISION
            elif mandate.state == assistant_mandate_state.SUPERVISION:
                mandate.state = assistant_mandate_state.VICE_RECTOR
            elif mandate.state == assistant_mandate_state.VICE_RECTOR:
                mandate.state = assistant_mandate_state.DONE
            mandate.save()
            if current_review.reviewer is not None:
                return HttpResponseRedirect(reverse("reviewer_mandates_list"))
            else:
                return HttpResponseRedirect(reverse("phd_supervisor_assistants_list"))
        elif 'save' in request.POST:
            current_review.status = review_status.IN_PROGRESS
            current_review.save()
            return review_edit(request, mandate_id)
    else:
        return render(request, "review_form.html", {'review': rev, 'role': mandate.state,
                                                    'year': mandate.academic_year.year + 1,
                                                    'absences': mandate.absences, 'comment': mandate.comment,
                                                    'mandate_id': mandate.id, 'form': form})


@login_required
def pst_form_view(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    try:
        current_reviewer = reviewer.find_by_person(request.user.person)
        current_role = current_reviewer.role
    except:
        current_reviewer = None
        current_role = reviewer_role.PHD_SUPERVISOR
    learning_units = tutoring_learning_unit_year.find_by_mandate(mandate)
    assistant = mandate.assistant
    menu = generate_reviewer_menu_tabs(current_role, mandate, None)
    return render(request, 'pst_form_view.html', {'menu': menu,
                                                  'menu_type': 'reviewer_menu',
                                                  'mandate_id': mandate.id,
                                                  'assistant': assistant, 'mandate': mandate,
                                                  'learning_units': learning_units,
                                                  'role': current_role,
                                                  'year': mandate.academic_year.year + 1})


def generate_reviewer_menu_tabs(role, mandate, active_item: None):
    if active_item:
        active_item = re.sub('_ASSISTANT', '', active_item)
    menu = []
    mandate_states = {}
    if mandate.assistant.supervisor:
        mandate_states.update({assistant_mandate_state.PHD_SUPERVISOR: 1})
    if mandate_structure.find_by_mandate_and_type(mandate, structure_type.INSTITUTE):
        mandate_states.update({assistant_mandate_state.RESEARCH: 2,
                               assistant_mandate_state.SUPERVISION: 3,
                               assistant_mandate_state.VICE_RECTOR: 4})
    else:
        mandate_states.update({assistant_mandate_state.SUPERVISION: 3,
                               assistant_mandate_state.VICE_RECTOR: 4})
    if role == reviewer_role.PHD_SUPERVISOR:
        try:
            latest_review_done = review.find_done_by_supervisor_for_mandate(mandate)
            if latest_review_done.status == review_status.DONE:
                review_is_done = True
            else:
                review_is_done = False
        except ObjectDoesNotExist:
            review_is_done = False
    else:
        latest_review_done = review.find_review_for_mandate_by_role(mandate, role)
    review_is_done = latest_review_done.status == review_status.DONE
    for state, order in sorted(mandate_states.items()):
        if role == reviewer_role.PHD_SUPERVISOR \
                and (state == assistant_mandate_state.RESEARCH
                     or state == assistant_mandate_state.SUPERVISION):
            break
        if state == role and review_is_done is False:
            if active_item == state:
                menu.append({'item': state, 'class': 'active', 'action': 'edit'})
            else:
                menu.append({'item': state, 'class': '', 'action': 'edit'})
        if mandate.state == state:
            break
        elif active_item == state:
            menu.append({'item': state, 'class': 'active', 'action': 'view'})
        else:
            menu.append({'item': state, 'class': '', 'action': 'view'})
    return menu
