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
from django.http.response import HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
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
import re


def user_is_reviewer(user):
    try:
        if user.is_authenticated():
            return reviewer.find_by_person(user.person)
    except ObjectDoesNotExist:
        return False


@user_passes_test(user_is_reviewer, login_url='assistants_home')
def review_view(request, mandate_id, role):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = reviewer.find_by_person(request.user.person)
    if reviewer.can_view_review(current_reviewer.id, mandate, role) == False:
        return HttpResponseRedirect(reverse('access_denied'))
    assistant = mandate.assistant
    if role == reviewer_role.PHD_SUPERVISOR:
        current_review = review.find_done_by_supervisor_for_mandate(mandate)
    else:
        current_reviews = review.find_review_for_mandate_by_role(mandate, role, 'DONE')
        current_review = current_reviews.reverse()[0]
    menu = generate_reviewer_menu_tabs(reviewer.find_roles_for_mandates(current_reviewer, mandate), mandate, role)
    return render(request, 'review_view.html', {'review': current_review,
                                                'role': role,
                                                'mandate_id': mandate.id,
                                                'reviewer': current_reviewer,
                                                'mandate_state': mandate.state,
                                                'assistant': assistant,
                                                'menu': menu,
                                                'year': mandate.academic_year.year + 1
                                                })


@user_passes_test(user_is_reviewer, login_url='assistants_home')
def review_edit(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = None
    existing_review = None
    try:
        current_reviewer = reviewer.can_edit_review(reviewer.find_by_person(person.find_by_user(request.user)).
                                                    id, mandate_id)
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('assistants_home'))
    existing_reviews = review.find_review_for_mandate_by_role(mandate, current_reviewer.role, 'IN_PROGRESS')
    if len(existing_reviews) > 0:
        existing_review = existing_reviews.reverse()[0]
    else:
        existing_review, created = review.Review.objects.get_or_create(
            mandate=mandate,
            reviewer=current_reviewer,
            status='IN_PROGRESS'
        )
    if current_reviewer.is_phd_supervisor and mandate.state == 'PHD_SUPERVISOR':
        current_role = 'PHD_SUPERVISOR'
    else:
        current_role = current_reviewer.role
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    assistant = mandate.assistant
    menu = generate_reviewer_menu_tabs(reviewer.find_roles_for_mandates(current_reviewer, mandate),
                                       mandate, current_role)
    form = ReviewForm(initial={'mandate': mandate,
                               'reviewer': existing_review.reviewer,
                               'status': existing_review.status,
                               'advice': existing_review.advice,
                               'changed': timezone.now,
                               'confidential': existing_review.confidential,
                               'remark': existing_review.remark
                               }, prefix="rev", instance=existing_review)
    return render(request, 'review_form.html', {'review': existing_review,
                                                'role': current_role,
                                                'year': mandate.academic_year.year + 1,
                                                'absences': mandate.absences,
                                                'comment': mandate.comment,
                                                'mandate_id': mandate.id,
                                                'previous_mandates': previous_mandates,
                                                'assistant': assistant,
                                                'mandate_state': mandate.state,
                                                'reviewer': current_reviewer,
                                                'menu': menu,
                                                'form': form})


@user_passes_test(user_is_reviewer, login_url='assistants_home')
def review_save(request, review_id, mandate_id):
    rev = review.find_by_id(review_id)
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    form = ReviewForm(data=request.POST, instance=rev, prefix='rev')
    if form.is_valid():
        current_review = form.save(commit=False)
        if 'validate_and_submit' in request.POST:
            current_review.status = "DONE"
            current_review.save()
            if mandate.state == "PHD_SUPERVISOR":
                if mandate_structure.find_by_mandate_and_type(mandate, 'INSTITUTE'):
                    mandate.state = "RESEARCH"
                elif mandate_structure.find_by_mandate_and_part_of_type(mandate, 'INSTITUTE'):
                    mandate.state = "RESEARCH"
                else:
                    mandate.state = "SUPERVISION"
            elif mandate.state == "RESEARCH":
                mandate.state = "SUPERVISION"
            elif mandate.state == "SUPERVISION":
                mandate.state = "VICE_RECTOR"
            elif mandate.state == "VICE_RECTOR":
                mandate.state = "DONE"
            mandate.save()
            return HttpResponseRedirect(reverse("reviewer_mandates_list"))
        elif 'save' in request.POST:
            current_review.status = "IN_PROGRESS"
            current_review.save()
            return review_edit(request, mandate_id)
    else:
        return render(request, "review_form.html", {'review': rev, 'role': mandate.state,
                                                    'year': mandate.academic_year.year + 1,
                                                    'absences': mandate.absences, 'comment': mandate.comment,
                                                    'mandate_id': mandate.id, 'form': form})


@user_passes_test(user_is_reviewer, login_url='assistants_home')
def pst_form_view(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = reviewer.find_by_person(person.find_by_user(request.user))
    learning_units = tutoring_learning_unit_year.find_by_mandate(mandate)
    assistant = mandate.assistant
    menu = generate_reviewer_menu_tabs(reviewer.find_roles_for_mandates(current_reviewer, mandate), mandate, 'PST')
    return render(request, 'pst_form_view.html', {'role': current_reviewer.role,
                                                  'mandate_id': mandate.id, 'mandate_state': mandate.state,
                                                  'assistant': assistant, 'mandate': mandate,
                                                  'learning_units': learning_units,
                                                  'reviewer': current_reviewer,
                                                  'menu': menu,
                                                  'year': mandate.academic_year.year + 1})


def generate_reviewer_menu_tabs(reviewer_roles_for_mandate, mandate, active_item):
    active_item = re.sub('_ASSISTANT', '', active_item)
    menu = []
    if mandate.assistant.supervisor:
        if mandate.state == 'RESEARCH' or mandate.state == 'SUPERVISION' or \
                        mandate.state == 'VICE_RECTOR' or mandate.state == 'DONE':
            if active_item == 'PHD_SUPERVISOR':
                menu.append({'item': 'PHD_SUPERVISOR', 'class': 'active', 'action': 'view'})
            else:
                menu.append({'item': 'PHD_SUPERVISOR', 'class': '', 'action': 'view'})
        elif mandate.state == 'PHD_SUPERVISOR' and reviewer_role.PHD_SUPERVISOR in reviewer_roles_for_mandate:
            if active_item == 'PHD_SUPERVISOR':
                menu.append({'item': 'PHD_SUPERVISOR', 'class': 'active', 'action': 'edit'})
            else:
                menu.append({'item': 'PHD_SUPERVISOR', 'class': '', 'action': 'edit'})
    if mandate_structure.find_by_mandate_and_type(mandate, structure_type.INSTITUTE):
        if mandate.state == 'SUPERVISION' or mandate.state == 'VICE_RECTOR' or mandate.state == 'DONE':
            if any(reviewer_role.RESEARCH in x for x in reviewer_roles_for_mandate) or \
                    any(reviewer_role.SUPERVISION in x for x in reviewer_roles_for_mandate) or \
                    any(reviewer_role.SECTOR_VICE_RECTOR in x for x in reviewer_roles_for_mandate):
                if active_item == 'RESEARCH':
                    menu.append({'item': 'RESEARCH', 'class': 'active', 'action': 'view'})
                else:
                    menu.append({'item': 'RESEARCH', 'class': '', 'action': 'view'})
            else:
                menu.append({'item': 'RESEARCH', 'class': 'disabled', 'action': ''})
        elif mandate.state == 'RESEARCH' and any(reviewer_role.RESEARCH in x for x in reviewer_roles_for_mandate):
            if active_item == 'RESEARCH':
                menu.append({'item': 'RESEARCH', 'class': 'active', 'action': 'edit'})
            else:
                menu.append({'item': 'RESEARCH', 'class': '', 'action': 'edit'})
        else:
            menu.append({'item': reviewer_role.RESEARCH, 'class': 'disabled', 'action': ''})
    if mandate.state == 'VICE_RECTOR' or mandate.state == 'DONE':
        if any(reviewer_role.SUPERVISION in x for x in reviewer_roles_for_mandate) or \
                any(reviewer_role.SECTOR_VICE_RECTOR in x for x in reviewer_roles_for_mandate):
            if active_item == 'SUPERVISION':
                menu.append({'item': 'SUPERVISION', 'class': 'active', 'action': 'view'})
            else:
                menu.append({'item': 'SUPERVISION', 'class': '', 'action': 'view'})
        else:
            menu.append({'item': 'SUPERVISION', 'class': 'disabled', 'action': ''})
    elif mandate.state == 'SUPERVISION' and any(reviewer_role.SUPERVISION in x for x in reviewer_roles_for_mandate):
        if active_item == 'SUPERVISION':
            menu.append({'item': 'SUPERVISION', 'class': 'active', 'action': 'edit'})
        else:
            menu.append({'item': 'SUPERVISION', 'class': '', 'action': 'edit'})
    else:
        menu.append({'item': 'SUPERVISION', 'class': 'disabled', 'action': ''})
    if mandate.state == 'DONE':
        if any(reviewer_role.SECTOR_VICE_RECTOR in x for x in reviewer_roles_for_mandate):
            if active_item == 'VICE_RECTOR':
                menu.append({'item': 'VICE_RECTOR', 'class': 'active', 'action': 'view'})
            else:
                menu.append({'item': 'VICE_RECTOR', 'class': '', 'action': 'view'})
        else:
            menu.append({'item': 'VICE_RECTOR', 'class': 'disabled', 'action': ''})
    elif mandate.state == 'VICE_RECTOR' and any(reviewer_role.SECTOR_VICE_RECTOR in x for x in
                                                reviewer_roles_for_mandate):
        if active_item == reviewer_role.SECTOR_VICE_RECTOR:
            menu.append({'item': 'VICE_RECTOR', 'class': 'active', 'action': 'edit'})
        else:
            menu.append({'item': 'VICE_RECTOR', 'class': '', 'action': 'edit'})
    else:
        menu.append({'item': 'VICE_RECTOR', 'class': 'disabled', 'action': ''})
    return menu
