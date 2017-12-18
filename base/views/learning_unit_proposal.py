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
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied


from base.business.learning_unit_proposal import compute_form_initial_data, compute_proposal_type, \
    is_eligible_for_modification_proposal
from base.forms.learning_unit_proposal import LearningUnitProposalModificationForm
from base.models.enums import proposal_state
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person


@login_required
@permission_required('base.can_propose_learningunit', raise_exception=True)
def propose_modification_of_learning_unit(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    user_person = get_object_or_404(Person, user=request.user)

    if not is_eligible_for_modification_proposal(learning_unit_year, user_person):
        raise PermissionDenied("Learning unit year not eligible for proposal or user has not sufficient rights.")

    initial_data = compute_form_initial_data(learning_unit_year)

    if request.method == 'POST':
        modified_post_data = request.POST.copy()
        modified_post_data["academic_year"] = str(learning_unit_year.academic_year.id)
        form = LearningUnitProposalModificationForm(modified_post_data, initial=initial_data)
        if form.is_valid():
            type_proposal = compute_proposal_type(form.initial, form.cleaned_data)
            form.save(learning_unit_year, user_person, type_proposal, proposal_state.ProposalState.FACULTY.name)
            messages.add_message(request, messages.SUCCESS,
                                 _("success_modification_proposal").format(type_proposal, learning_unit_year.acronym))
            return redirect('learning_unit', learning_unit_year_id=learning_unit_year.id)
    else:
        form = LearningUnitProposalModificationForm(initial=initial_data)

    return render(request, 'proposal/learning_unit_modification.html', {'learning_unit_year': learning_unit_year,
                                                                        'person': user_person,
                                                                        'form': form,
                                                                        'experimental_phase': True})
