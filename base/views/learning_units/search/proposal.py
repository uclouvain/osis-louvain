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
    _create_xls_proposal_comparison, BaseLearningUnitSearch, SearchTypes
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer

ACTION_BACK_TO_INITIAL = "back_to_initial"
ACTION_CONSOLIDATE = "consolidate"
ACTION_FORCE_STATE = "force_state"


@RenderToExcel("xls", _create_xls_proposal)
@RenderToExcel("xls_comparison", _create_xls_proposal_comparison)
class SearchLearningUnitProposal(BaseLearningUnitSearch):
    template_name = "learning_unit/search/proposal.html"
    search_type = SearchTypes.PROPOSAL_SEARCH
    filterset_class = ProposalLearningUnitFilter
    serializer_class = LearningUnitDetailedSerializer

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
