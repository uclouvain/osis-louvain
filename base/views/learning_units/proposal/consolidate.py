##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import http
from django.contrib.auth.decorators import login_required
from django.contrib.messages import ERROR
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from waffle.decorators import waffle_flag

from base.business import learning_unit_proposal as business_proposal
from base.business.learning_units import perms
from base.models.enums import proposal_type, proposal_state
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.common import display_error_messages, display_messages_by_level


@waffle_flag('learning_unit_proposal_delete')
@login_required
@require_POST
def consolidate_proposal(request: http.HttpRequest, learning_unit_year_id: int):
    proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year__id=learning_unit_year_id)
    user_person = get_object_or_404(Person, user=request.user)

    if not perms.is_eligible_to_consolidate_proposal(proposal, user_person):
        raise PermissionDenied("Proposal cannot be consolidated")

    messages_by_level = {}
    try:
        messages_by_level = business_proposal.consolidate_proposals_and_send_report([proposal], user_person, {})
        display_messages_by_level(request, messages_by_level)
    except IntegrityError as e:
        display_error_messages(request, e.args[0])

    if proposal.type == proposal_type.ProposalType.CREATION.name and \
            proposal.state == proposal_state.ProposalState.REFUSED.name and not messages_by_level.get(ERROR, []):
        return redirect('learning_units')

    if proposal.type == proposal_type.ProposalType.SUPPRESSION.name and not messages_by_level.get(ERROR, []):
        to_redirect_luy = proposal.learning_unit_year.get_learning_unit_previous_year()
        if to_redirect_luy:
            return redirect('learning_unit', learning_unit_year_id=to_redirect_luy.id)
        else:
            return redirect('learning_units')
    return redirect('learning_unit', learning_unit_year_id=proposal.learning_unit_year.id)
