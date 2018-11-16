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
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from waffle.decorators import waffle_flag

from base.business.learning_unit_proposal import compute_proposal_state
from base.forms.learning_unit.edition import LearningUnitEndDateForm
from base.forms.learning_unit_proposal import ProposalLearningUnitForm, ProposalBaseForm
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views import layout
from base.views.common import display_success_messages
from base.views.learning_units import perms
from base.views.learning_units.common import get_learning_unit_identification_context


@waffle_flag('learning_unit_proposal_update')
@login_required
@perms.can_create_modification_proposal
@permission_required('base.can_propose_learningunit', raise_exception=True)
def learning_unit_modification_proposal(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    return _update_or_create_proposal(request, learning_unit_year)


@waffle_flag('learning_unit_proposal_update')
@login_required
@perms.can_create_modification_proposal
@permission_required('base.can_propose_learningunit', raise_exception=True)
def learning_unit_suppression_proposal(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, id=learning_unit_year_id)
    return _update_or_create_suppression_proposal(request, learning_unit_year)


@waffle_flag('learning_unit_proposal_update')
@login_required
@perms.can_edit_learning_unit_proposal
def update_learning_unit_proposal(request, learning_unit_year_id):
    proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year=learning_unit_year_id)

    if proposal.type == ProposalType.SUPPRESSION.name:
        return _update_or_create_suppression_proposal(request, proposal.learning_unit_year, proposal)
    else:
        return _update_or_create_proposal(request, proposal.learning_unit_year, proposal)


def _update_or_create_proposal(request, learning_unit_year, proposal=None):
    person = get_object_or_404(Person, user=request.user)

    proposal_base_form = ProposalBaseForm(request.POST or None, person, learning_unit_year, proposal)

    if proposal_base_form.is_valid():
        proposal = proposal_base_form.save()
        display_success_messages(
            request, _("You proposed a modification of type {} for the learning unit {}.").format(
                _(proposal.type), learning_unit_year.acronym)
        )
        return redirect('learning_unit', learning_unit_year_id=learning_unit_year.id)

    context = proposal_base_form.get_context()
    if proposal:
        return layout.render(request, 'learning_unit/proposal/update_modification.html', context)
    return layout.render(request, 'learning_unit/proposal/create_modification.html', context)


def _update_or_create_suppression_proposal(request, learning_unit_year, proposal=None):
    person = get_object_or_404(Person, user=request.user)

    proposal_type = ProposalType.SUPPRESSION.name
    initial = _get_initial(learning_unit_year, proposal, person, proposal_type=proposal_type)

    max_year = _get_max_year(learning_unit_year, proposal)

    form_end_date = LearningUnitEndDateForm(request.POST or None, learning_unit_year, max_year=max_year)
    form_proposal = ProposalLearningUnitForm(request.POST or None, person=person, instance=proposal,
                                             initial=initial)

    if form_end_date.is_valid() and form_proposal.is_valid():
        with transaction.atomic():
            form_proposal.save()

            # For the proposal, we do not update learning_unit_year
            form_end_date.save(update_learning_unit_year=False)

            display_success_messages(
                request, _("You proposed a modification of type {} for the learning unit {}.").format(
                    _(proposal_type), learning_unit_year.acronym)
            )

        return redirect('learning_unit', learning_unit_year_id=learning_unit_year.id)

    context = get_learning_unit_identification_context(learning_unit_year.id, person)
    context.update({
        'person': person,
        'form_end_date': form_end_date,
        'form_proposal': form_proposal,
        'experimental_phase': True})
    if proposal:
        return layout.render(request, 'learning_unit/proposal/update_suppression.html', context)
    return layout.render(request, 'learning_unit/proposal/create_suppression.html', context)


def _get_max_year(learning_unit_year, proposal):
    return proposal.initial_data.get('end_year') if proposal else learning_unit_year.learning_unit.end_year


def _get_initial(learning_unit_year, proposal, user_person, proposal_type=ProposalType.TRANSFORMATION.name):
    initial = {
            'learning_unit_year': learning_unit_year,
            'type': proposal_type,
            'state': compute_proposal_state(user_person),
            'author': user_person
    }
    if proposal:
        initial['type'] = proposal.type
        initial['state'] = proposal.state
    return initial
