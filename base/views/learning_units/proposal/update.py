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
import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.business import learning_unit_proposal as business_proposal
from base.business.learning_unit_proposal import get_difference_of_proposal
from base.business.learning_units.proposal.common import compute_proposal_state
from base.forms.learning_unit.edition import LearningUnitEndDateForm
from base.forms.learning_unit_proposal import LearningUnitProposalModificationForm, ProposalLearningUnitForm
from base.models import proposal_learning_unit
from base.models.entity_version import find_latest_version_by_entity
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views import layout
from base.views.common import display_success_messages, display_error_messages
from base.views.learning_unit import compute_form_initial_data, get_learning_unit_identification_context
from base.views.learning_units import perms


# FIXME : Merge create_modification and update_modification
@login_required
@perms.can_create_modification_proposal
@permission_required('base.can_propose_learningunit', raise_exception=True)
def learning_unit_modification_proposal(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    user_person = get_object_or_404(Person, user=request.user)
    initial_data = compute_form_initial_data(learning_unit_year)
    proposal = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year)

    form = LearningUnitProposalModificationForm(
        request.POST or None,
        initial=initial_data,
        instance=proposal,
        learning_unit=learning_unit_year.learning_unit
    )

    if form.is_valid():
        type_proposal = business_proposal.compute_proposal_type(initial_data, request.POST)
        with transaction.atomic():
            form.save(learning_unit_year, user_person, type_proposal, compute_proposal_state(user_person))
            save_proposal_type(learning_unit_year.proposallearningunit, request)

        display_success_messages(request, _("success_modification_proposal").format(
            _(type_proposal), learning_unit_year.acronym))

        return redirect('learning_unit', learning_unit_year_id=learning_unit_year.id)

    return layout.render(request, 'learning_unit/proposal/create_modification_proposal.html', {
        'learning_unit_year': learning_unit_year, 'person': user_person, 'form': form, 'experimental_phase': True})


@login_required
@perms.can_create_modification_proposal
@permission_required('base.can_propose_learningunit', raise_exception=True)
def learning_unit_suppression_proposal(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    user_person = get_object_or_404(Person, user=request.user)
    return _update_or_create_suppression_proposal(request, user_person, learning_unit_year)


@login_required
@perms.can_edit_learning_unit_proposal
def update_learning_unit_proposal(request, learning_unit_year_id):
    user_person = get_object_or_404(Person, user=request.user)
    proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year=learning_unit_year_id)

    if proposal.type == ProposalType.SUPPRESSION.name:
        return _update_or_create_suppression_proposal(request, user_person, proposal.learning_unit_year, proposal)
    else:
        return _update_proposal(request, user_person, proposal)


def _update_proposal(request, user_person, proposal):
    initial_data = compute_form_initial_data(proposal.learning_unit_year)
    initial_data.update(_build_proposal_data(proposal))

    proposal_form = LearningUnitProposalModificationForm(
        request.POST or None,
        initial=initial_data,
        instance=proposal,
        learning_unit=proposal.learning_unit_year.learning_unit
    )

    if proposal_form.is_valid():
        try:
            type_proposal = business_proposal.compute_proposal_type(initial_data, request.POST)

            proposal_form.save(proposal.learning_unit_year, user_person, type_proposal,
                               proposal_form.cleaned_data.get("state"))

            save_proposal_type(proposal, request)

            display_success_messages(request, _("proposal_edited_successfully"))
            return HttpResponseRedirect(reverse('learning_unit', args=[proposal.learning_unit_year.id]))
        except (IntegrityError, ValueError) as e:
            display_error_messages(request, e.args[0])

    return layout.render(request, 'learning_unit/proposal/edition.html',  {
        'learning_unit_year': proposal.learning_unit_year,
        'person': user_person,
        'form': proposal_form,
        'experimental_phase': True})


def save_proposal_type(proposal, request):
    # FIXME : Needs refactoring ! This method works around the buggy save()
    initial_data = get_difference_of_proposal(proposal)
    type_proposal = business_proposal.compute_proposal_type(initial_data, request.POST)
    proposal.type = type_proposal
    proposal.save()


def _update_or_create_suppression_proposal(request, person, learning_unit_year, proposal=None):
    type_proposal = ProposalType.SUPPRESSION.name
    initial = _get_initial(learning_unit_year, proposal, type_proposal, person)

    max_year = _get_max_year(learning_unit_year, proposal)

    form_end_date = LearningUnitEndDateForm(request.POST or None, learning_unit_year.learning_unit, max_year=max_year)
    form_proposal = ProposalLearningUnitForm(request.POST or None, instance=proposal, initial=initial)

    if form_end_date.is_valid() and form_proposal.is_valid():
        with transaction.atomic():
            form_proposal.save()

            # For the proposal, we do not update learning_unit_year
            form_end_date.save(update_learning_unit_year=False)

            display_success_messages(
                request, _("success_modification_proposal").format(_(type_proposal), learning_unit_year.acronym))

        return redirect('learning_unit', learning_unit_year_id=learning_unit_year.id)

    context = get_learning_unit_identification_context(learning_unit_year.id, person)
    context.update({
        'person': person,
        'form_end_date': form_end_date,
        'form_proposal': form_proposal,
        'experimental_phase': True})
    return layout.render(request, 'learning_unit/proposal/create_suppression_proposal.html', context)


def _get_max_year(learning_unit_year, proposal):
    return proposal.initial_data.get('end_year') if proposal else learning_unit_year.learning_unit.end_year


def _get_initial(learning_unit_year, proposal, type_proposal, user_person):
    if not proposal:
        return {
            'learning_unit_year': learning_unit_year,
            'type': type_proposal,
            'state': compute_proposal_state(user_person),
            'author': user_person
        }


def _build_proposal_data(proposal):
    return {"folder_id": proposal.folder_id,
            "entity": find_latest_version_by_entity(proposal.entity.id, datetime.date.today()),
            "type": proposal.type,
            "state": proposal.state}
