##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.messages import WARNING
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.business import learning_unit_proposal as proposal_business
from base.forms.learning_unit.comparison import SelectComparisonYears
from base.forms.proposal.learning_unit_proposal import ProposalStateModelForm, \
    ProposalLearningUnitFilter
from base.forms.search.search_form import get_research_criteria
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.utils.search import RenderToExcel
from base.views.common import display_messages_by_level
from base.views.learning_units.search.common import _create_xls_proposal, \
    _create_xls_proposal_comparison, BaseLearningUnitSearch, SearchTypes, _create_xls_with_parameters, \
    _create_xls_attributions, _create_xls_ue_utilizations_with_one_training_per_line, \
    _create_xls_educational_specifications
from learning_unit.api.serializers.learning_unit import LearningUnitSearchSerializer

ACTION_BACK_TO_INITIAL = "back_to_initial"
ACTION_CONSOLIDATE = "consolidate"
ACTION_FORCE_STATE = "force_state"


@RenderToExcel("xls", _create_xls_proposal)
@RenderToExcel("xls_comparison", _create_xls_proposal_comparison)
@RenderToExcel("xls_with_parameters", _create_xls_with_parameters)
@RenderToExcel("xls_one_pgm_per_line", _create_xls_ue_utilizations_with_one_training_per_line)
@RenderToExcel("xls_attributions", _create_xls_attributions)
@RenderToExcel("xls_educational_specifications", _create_xls_educational_specifications)
class SearchLearningUnitProposal(BaseLearningUnitSearch):
    template_name = "learning_unit/search/proposal.html"
    search_type = SearchTypes.PROPOSAL_SEARCH
    filterset_class = ProposalLearningUnitFilter
    serializer_class = LearningUnitSearchSerializer

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["person"] = get_object_or_404(Person, user=self.request.user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context["form"]
        select_comparison_form_academic_year = context["proposal_academic_year"]
        if form.is_valid():
            select_comparison_form_academic_year = form.cleaned_data["academic_year"] or \
                                                   select_comparison_form_academic_year
        user_person = get_object_or_404(Person, user=self.request.user)
        context.update({
            'form_proposal_state': ProposalStateModelForm(is_faculty_manager=user_person.is_faculty_manager),
            'can_change_proposal_state': user_person.is_faculty_manager or user_person.is_central_manager,
            "form_comparison": SelectComparisonYears(academic_year=select_comparison_form_academic_year),
        })
        return context

    def post(self, request, *args, **kwargs):
        user_person = get_object_or_404(Person, user=self.request.user)

        search_form = ProposalLearningUnitFilter(request.GET or None, person=user_person)
        research_criteria = get_research_criteria(search_form.form) if search_form.is_valid() else []

        selected_proposals_acronym = request.POST.getlist("selected_action", default=[])
        selected_proposals = ProposalLearningUnit.objects.filter(
            learning_unit_year__acronym__in=selected_proposals_acronym
        )
        messages_by_level = apply_action_on_proposals(selected_proposals, user_person, request.POST, research_criteria)
        display_messages_by_level(request, messages_by_level)
        return redirect(reverse("learning_unit_proposal_search") + "?{}".format(request.GET.urlencode()))


def apply_action_on_proposals(proposals, author, post_data, research_criteria):
    if not bool(proposals):
        return {WARNING: [_("No proposals was selected.")]}

    action = post_data.get("action", "")
    messages_by_level = {}
    if action == ACTION_BACK_TO_INITIAL:
        messages_by_level = proposal_business.cancel_proposals_and_send_report(proposals, author, research_criteria)
    elif action == ACTION_CONSOLIDATE:
        messages_by_level = proposal_business.consolidate_proposals_and_send_report(proposals, author,
                                                                                    research_criteria)
    elif action == ACTION_FORCE_STATE:
        form = ProposalStateModelForm(post_data)
        if form.is_valid():
            new_state = form.cleaned_data.get("state")
            messages_by_level = proposal_business.force_state_of_proposals(proposals, author, new_state)
    return messages_by_level
