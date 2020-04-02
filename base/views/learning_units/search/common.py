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
from enum import Enum

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.business import learning_unit_year_with_context
from base.business.learning_unit_xls import create_xls, create_xls_with_parameters, WITH_GRP, WITH_ATTRIBUTIONS, \
    create_xls_attributions
from base.business.learning_units.xls_comparison import create_xls_comparison, create_xls_proposal_comparison
from base.business.learning_units.xls_educational_information_and_specifications import \
    create_xls_educational_information_and_specifications
from base.business.proposal_xls import create_xls as create_xls_proposal
from base.forms.search.search_form import get_research_criteria
from base.models.academic_year import starting_academic_year
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin
from base.views.common import remove_from_session


class SearchTypes(Enum):
    SIMPLE_SEARCH = 1
    SERVICE_COURSES_SEARCH = 2
    PROPOSAL_SEARCH = 3
    SUMMARY_LIST = 4
    BORROWED_COURSE = 5
    EXTERNAL_SEARCH = 6


class BaseLearningUnitSearch(PermissionRequiredMixin, CacheFilterMixin, SearchMixin, FilterView):
    model = LearningUnitYear
    template_name = None
    raise_exception = True
    search_type = None

    filterset_class = None
    permission_required = 'base.can_access_learningunit'
    cache_exclude_params = ['xls_status']

    serializer_class = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self._save_search_type_in_session()

        starting_ac = starting_academic_year()
        if context["paginator"].count == 0 and self.request.GET:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        context.update({
            'form': context["filter"].form,
            'learning_units_count': context["paginator"].count,
            'current_academic_year': starting_ac,
            'proposal_academic_year': starting_ac.next(),
            'search_type': self.search_type.value,
            'items_per_page': context["paginator"].per_page,
        })
        return context

    def _save_search_type_in_session(self):
        remove_from_session(self.request, 'search_url')
        if self.search_type == SearchTypes.EXTERNAL_SEARCH:
            self.request.session['ue_search_type'] = str(_('External learning units'))
        elif self.search_type == SearchTypes.SIMPLE_SEARCH:
            self.request.session['ue_search_type'] = None
        else:
            self.request.session['ue_search_type'] = str(_get_search_type_label(self.search_type))


def _get_filter(form, search_type):
    criterias = itertools.chain([(_('Search type'), _get_search_type_label(search_type))], get_research_criteria(form))
    return collections.OrderedDict(criterias)


def _get_search_type_label(search_type):
    return {
        SearchTypes.PROPOSAL_SEARCH: _('Proposals'),
        SearchTypes.SERVICE_COURSES_SEARCH: _('Service courses'),
        SearchTypes.BORROWED_COURSE: _('Borrowed courses')
    }.get(search_type, _('Learning units'))


def _create_xls(view_obj, context, **response_kwargs):
    return __create(context, view_obj, create_xls)


def __create(context, view_obj, method):
    user = view_obj.request.user
    luys = context["filter"].qs
    filters = _get_filter(context["form"], view_obj.search_type)
    return method(user, luys, filters)


def _create_xls_educational_specifications(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    luys = context["filter"].qs
    return create_xls_educational_information_and_specifications(user, luys, view_obj.request)


def _create_xls_comparison(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    luys = context["filter"].qs
    filters = _get_filter(context["form"], view_obj.search_type)
    comparison_year = view_obj.request.GET.get('comparison_year')
    return create_xls_comparison(user, luys, filters, comparison_year)


def _create_xls_with_parameters(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    luys = context["filter"].qs
    filters = _get_filter(context["form"], view_obj.search_type)
    other_params = {
        WITH_GRP: view_obj.request.GET.get('with_grp') == 'true',
        WITH_ATTRIBUTIONS: view_obj.request.GET.get('with_attributions') == 'true'
    }
    return create_xls_with_parameters(user, luys, filters, other_params)


def _create_xls_attributions(view_obj, context, **response_kwargs):
    return __create(context, view_obj, create_xls_attributions)


def _create_xls_proposal(view_obj, context, **response_kwargs):
    return __create(context, view_obj, create_xls_proposal)


def _create_xls_proposal_comparison(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    luys = context["filter"].qs
    for luy in luys:
        learning_unit_year_with_context.append_latest_entities(luy, service_course_search=False)
    filters = _get_filter(context["form"], view_obj.search_type)
    return create_xls_proposal_comparison(user, luys, filters)
