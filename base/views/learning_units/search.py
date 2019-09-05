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
import collections
import itertools

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.messages import WARNING
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.business import learning_unit_proposal as proposal_business
from base.business.learning_unit_xls import create_xls_with_parameters, WITH_ATTRIBUTIONS, WITH_GRP, \
    create_xls_attributions, create_xls
from base.business.learning_units.xls_comparison import create_xls_comparison, get_academic_year_of_reference, \
    create_xls_proposal_comparison
from base.business.proposal_xls import create_xls as create_xls_proposal
from base.forms.common import TooManyResultsException
from base.forms.learning_unit.comparison import SelectComparisonYears
from base.forms.learning_unit.search_form import LearningUnitYearForm, ExternalLearningUnitYearForm
from base.forms.proposal.learning_unit_proposal import LearningUnitProposalForm, ProposalStateModelForm
from base.forms.search.search_form import get_research_criteria
from base.models.academic_year import get_last_academic_years, starting_academic_year
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.utils.cache import cache_filter
from base.views.common import check_if_display_message, display_messages_by_level, display_error_messages, \
    paginate_queryset

SIMPLE_SEARCH = 1
SERVICE_COURSES_SEARCH = 2
PROPOSAL_SEARCH = 3
SUMMARY_LIST = 4
BORROWED_COURSE = 5
EXTERNAL_SEARCH = 6

ACTION_BACK_TO_INITIAL = "back_to_initial"
ACTION_CONSOLIDATE = "consolidate"
ACTION_FORCE_STATE = "force_state"

ITEMS_PER_PAGES = 2000


def learning_units_search(request, search_type):
    service_course_search = search_type == SERVICE_COURSES_SEARCH
    borrowed_course_search = search_type == BORROWED_COURSE

    form = LearningUnitYearForm(
        request.GET or None,
        service_course_search=service_course_search,
        borrowed_course_search=borrowed_course_search,
        initial={'academic_year_id': starting_academic_year(), 'with_entity_subordinated': True}
    )
    found_learning_units = LearningUnitYear.objects.none()
    try:
        if form.is_valid():
            found_learning_units = form.get_activity_learning_units()
            check_if_display_message(request, found_learning_units)

    except TooManyResultsException:
        display_error_messages(request, _('Too many results'))
    if request.POST.get('xls_status') == "xls":
        return create_xls(request.user, found_learning_units, _get_filter(form, search_type))

    if request.POST.get('xls_status') == "xls_comparison":
        return create_xls_comparison(
            request.user,
            found_learning_units,
            _get_filter(form, search_type),
            request.POST.get('comparison_year')
        )

    if request.POST.get('xls_status') == "xls_with_parameters":
        return create_xls_with_parameters(
            request.user,
            found_learning_units,
            _get_filter(form, search_type),
            {
                WITH_GRP: request.POST.get('with_grp') == 'true',
                WITH_ATTRIBUTIONS: request.POST.get('with_attributions') == 'true'
            }
        )

    if request.POST.get('xls_status') == "xls_attributions":
        return create_xls_attributions(request.user, found_learning_units, _get_filter(form, search_type))

    form_comparison = SelectComparisonYears(academic_year=get_academic_year_of_reference(found_learning_units))
    starting_ac = starting_academic_year()
    context = {
        'form': form,
        'academic_years': get_last_academic_years(),
        'container_types': LearningContainerYearType.choices(),
        'types': learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        'learning_units_count': len(found_learning_units)
        if isinstance(found_learning_units, list) else
        found_learning_units.count(),
        'current_academic_year': starting_ac,
        'proposal_academic_year': starting_ac.next(),
        'search_type': search_type,
        'is_faculty_manager': request.user.person.is_faculty_manager,
        'form_comparison': form_comparison,
        'page_obj': paginate_queryset(found_learning_units, request.GET, items_per_page=ITEMS_PER_PAGES),
    }

    return render(request, "learning_units.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units(request):
    return learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_service_course(request):
    return learning_units_search(request, SERVICE_COURSES_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_borrowed_course(request):
    return learning_units_search(request, BORROWED_COURSE)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_proposal_search(request):
    user_person = get_object_or_404(Person, user=request.user)
    starting_ac_year = starting_academic_year()
    search_form = LearningUnitProposalForm(
        request.GET or None,
        person=user_person,
        initial={'academic_year_id': starting_ac_year, 'with_entity_subordinated': True},
    )
    found_learning_units = LearningUnitYear.objects.none()

    if search_form.is_valid():
        found_learning_units = search_form.get_proposal_learning_units()
        check_if_display_message(request, found_learning_units)

    if request.POST.get('xls_status_proposal') == "xls":
        return create_xls_proposal(
            user_person.user,
            list(found_learning_units),
            _get_filter(search_form, PROPOSAL_SEARCH)
        )

    if request.POST.get('xls_status_proposal') == "xls_comparison":
        return create_xls_proposal_comparison(
            user_person.user,
            list(found_learning_units),
            _get_filter(search_form, PROPOSAL_SEARCH)
        )

    if request.POST:
        research_criteria = get_research_criteria(search_form) if search_form.is_valid() else []

        selected_proposals_id = request.POST.getlist("selected_action", default=[])
        selected_proposals = ProposalLearningUnit.objects.filter(id__in=selected_proposals_id)
        messages_by_level = apply_action_on_proposals(selected_proposals, user_person, request.POST, research_criteria)
        display_messages_by_level(request, messages_by_level)
        return redirect(reverse("learning_unit_proposal_search") + "?{}".format(request.GET.urlencode()))

    context = {
        'form': search_form,
        'form_proposal_state': ProposalStateModelForm(is_faculty_manager=user_person.is_faculty_manager),
        'academic_years': get_last_academic_years(),
        'current_academic_year': starting_ac_year,
        'search_type': PROPOSAL_SEARCH,
        'learning_units_count': found_learning_units.count(),
        'can_change_proposal_state': user_person.is_faculty_manager or user_person.is_central_manager,
        'form_comparison': SelectComparisonYears(academic_year=get_academic_year_of_reference(found_learning_units)),
        'page_obj': paginate_queryset(found_learning_units, request.GET, items_per_page=ITEMS_PER_PAGES),
    }
    return render(request, "learning_units.html", context)


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


def _get_filter(form, search_type):
    criterias = itertools.chain([(_('Search type'), _get_search_type_label(search_type))], get_research_criteria(form))
    return collections.OrderedDict(criterias)


def _get_search_type_label(search_type):
    return {
        PROPOSAL_SEARCH: _('Proposals'),
        SERVICE_COURSES_SEARCH: _('Service courses'),
        BORROWED_COURSE: _('Borrowed courses')
    }.get(search_type, _('Learning units'))


@login_required
@permission_required('base.can_access_externallearningunityear', raise_exception=True)
@cache_filter()
def learning_units_external_search(request):
    starting_ac_year = starting_academic_year()
    search_form = ExternalLearningUnitYearForm(
        request.GET or None,
        initial={'academic_year_id': starting_ac_year, 'with_entity_subordinated': True}
    )
    user_person = get_object_or_404(Person, user=request.user)
    found_learning_units = LearningUnitYear.objects.none()

    if search_form.is_valid():
        found_learning_units = search_form.get_queryset()
        check_if_display_message(request, found_learning_units)

    context = {
        'form': search_form,
        'academic_years': get_last_academic_years(),
        'current_academic_year': starting_ac_year,
        'search_type': EXTERNAL_SEARCH,
        'learning_units_count': found_learning_units.count(),
        'is_faculty_manager': user_person.is_faculty_manager,
        'form_comparison': SelectComparisonYears(academic_year=get_academic_year_of_reference(found_learning_units)),
        'page_obj': paginate_queryset(found_learning_units, request.GET, items_per_page=ITEMS_PER_PAGES),
    }
    return render(request, "learning_units.html", context)
