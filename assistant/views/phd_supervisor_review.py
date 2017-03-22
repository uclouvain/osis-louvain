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
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from assistant.models import assistant_mandate, review, tutoring_learning_unit_year, mandate_structure
from django.core.exceptions import ObjectDoesNotExist
from assistant.enums import reviewer_role
from django.utils import timezone
from django.core.urlresolvers import reverse
from assistant.forms import ReviewForm
from assistant.models.enums import review_status


@login_required
def review_view(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_role = reviewer_role.PHD_SUPERVISOR
    try:
        current_review = review.find_done_by_supervisor_for_mandate(mandate)
    except ObjectDoesNotExist:
        current_review = None
    assistant = mandate.assistant
    menu = generate_phd_supervisor_menu_tabs(mandate, current_role)
    return render(request, 'review_view.html', {'review': current_review,
                                                'role': current_role,
                                                'menu': menu,
                                                'menu_type': 'phd_supervisor_menu',
                                                'mandate_id': mandate.id,
                                                'mandate_state': mandate.state,
                                                'assistant': assistant,
                                                'year': mandate.academic_year.year + 1
                                                })


@login_required
def review_edit(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = None
    try:
        review.find_done_by_supervisor_for_mandate(mandate)
        return HttpResponseRedirect(reverse("assistants_home"))
    except:
        existing_review, created = review.Review.objects.get_or_create(
            mandate=mandate,
            reviewer=None,
            status=review_status.IN_PROGRESS
        )
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    role = reviewer_role.PHD_SUPERVISOR
    menu = generate_phd_supervisor_menu_tabs(mandate, role)
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
                                                'menu_type': 'phd_supervisor_menu',
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
            if mandate_structure.find_by_mandate_and_type(mandate, 'INSTITUTE'):
                mandate.state = "RESEARCH"
            elif mandate_structure.find_by_mandate_and_part_of_type(mandate, 'INSTITUTE'):
                mandate.state = "RESEARCH"
            else:
                mandate.state = "SUPERVISION"
            mandate.save()
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
    current_role = reviewer_role.PHD_SUPERVISOR
    learning_units = tutoring_learning_unit_year.find_by_mandate(mandate)
    assistant = mandate.assistant
    menu = generate_phd_supervisor_menu_tabs(mandate, None)
    return render(request, 'pst_form_view.html', {'menu': menu,
                                                  'mandate_id': mandate.id,
                                                  'assistant': assistant, 'mandate': mandate,
                                                  'learning_units': learning_units,
                                                  'role': current_role,
                                                  'menu_type': 'phd_supervisor_menu',
                                                  'year': mandate.academic_year.year + 1})


def generate_phd_supervisor_menu_tabs(mandate, active_item: None):
    menu = []
    try:
        latest_review_done = review.find_done_by_supervisor_for_mandate(mandate)
        if latest_review_done.status == review_status.DONE:
            review_is_done = True
        else:
            review_is_done = False
    except ObjectDoesNotExist:
            review_is_done = False
    if review_is_done is False:
        if active_item == 'PHD_SUPERVISOR':
            menu.append({'item': 'PHD_SUPERVISOR', 'class': 'active', 'action': 'edit'})
        else:
            menu.append({'item': 'PHD_SUPERVISOR', 'class': '', 'action': 'edit'})
    else:
        if active_item == 'PHD_SUPERVISOR':
            menu.append({'item': 'PHD_SUPERVISOR', 'class': 'active', 'action': 'view'})
        else:
            menu.append({'item': 'PHD_SUPERVISOR', 'class': '', 'action': 'view'})
    return menu
