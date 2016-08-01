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
from django.contrib.auth.decorators import user_passes_test
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from assistant.models import assistant_mandate, review, reviewer, mandate_structure
from base.models import academic_year, structure, person
from assistant.forms import ReviewForm
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

def review_view(request, review_id):
    """Use to view an review."""

    current_review = review.find_by_id(review_id)
    mandate = assistant_mandate.find_mandate_by_id(current_review.mandate.id)
    reviews = review.find_by_mandate(mandate.id)
    links = [[None,False], [None,False], [None,False], [None,False]]
    for rev in reviews:
        if rev.reviewer == None:
            if rev == current_review:
                links[0] = [rev.id, True]
            else:
                links[0] = [rev.id, False]
        elif "RESEARCH" in rev.reviewer.role:
            if rev == current_review:
                links[1] = [rev.id, True]
            else:
                links[1] = [rev.id, False]
        elif "SUPERVISION" in rev.reviewer.role:
            if rev == current_review:
                links[2] = [rev.id, True]
            else:
                links[2] = [rev.id, False]
        elif "SECTOR_VICE_RECTOR" in rev.reviewer.role:
            if rev == current_review:
                links[3] = [rev.id, True]
            else:
                links[3] = [rev.id, False]
    return render(request, 'review_view.html', {'review': current_review,
                                                'role': mandate.state,
                                                'links': links,
                                                'mandate_id': mandate.id,
                                                'year': mandate.academic_year.year +1})

def review_edit(request, mandate_id):
    """Use to add an reviewer review."""
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_reviewer = reviewer.canEditReview(reviewer.find_by_person(person.find_by_user(request.user)).
                                                  id, mandate_id)
    if current_reviewer == None:
        if mandate.assistant.supervisor and mandate.assistant.supervisor == person.find_by_user(request.user) \
                and mandate.state == "PHD_SUPERVISOR":
            return True
        else:
            return HttpResponseRedirect(reverse('assistants_home'))
    r, created = review.Review.objects.get_or_create(
        mandate=mandate,
        reviewer=current_reviewer,
        status='IN_PROGRESS'
    )
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    reviews = review.find_by_mandate(mandate).filter(status = "DONE")
    links = [None,None,None,None]
    for rev in reviews:
        if rev.reviewer == None:
            links[0]=rev.id
        elif "RESEARCH" in rev.reviewer.role:
            links[1] = rev.id
        elif "SUPERVISION" in rev.reviewer.role:
            links[2] = rev.id
        elif "SECTOR_VICE_RECTOR" in rev.reviewer.role:
            links[3] = rev.id
    try:
        role = current_reviewer.role
    except:
        role="PHD_SUPERVISOR"
    form = ReviewForm(initial={'mandate': mandate,
                               'reviewer': r.reviewer,
                               'status': r.status,
                               'advice': r.advice,
                               'changed': timezone.now,
                               'confidential': r.confidential,
                               'remark': r.remark,
                               'justification': r.justification
                                }, prefix="rev", instance=r)
    return render(request, 'review_form.html', {'review': r,
                                                'role': role,
                                                'year': mandate.academic_year.year +1,
                                                'absences': mandate.absences,
                                                'comment': mandate.comment,
                                                'mandate_id': mandate.id,
                                                'previous_mandates': previous_mandates,
                                                'links': links,
                                                'form': form})

def review_save(request, review_id, mandate_id):
    """Use to save an reviewer review."""
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
        return render(request, "review_form.html", {'review': rev,
                                                'role': mandate.state,
                                                'year': mandate.academic_year.year +1,
                                                'absences': mandate.absences,
                                                'comment': mandate.comment,
                                                'mandate_id': mandate.id,
                                                'form': form})
