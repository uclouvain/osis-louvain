############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
from django.db.models import Window
from django.db.models.functions import Lag, Lead
from django.template.defaulttags import register
from django.urls import reverse

from base.forms.education_groups import EducationGroupFilter
from base.forms.learning_unit.search.borrowed import BorrowedLearningUnitSearch
from base.forms.learning_unit.search.educational_information import LearningUnitDescriptionFicheFilter
from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.forms.learning_unit.search.service_course import ServiceCourseFilter
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.forms.proposal.learning_unit_proposal import ProposalLearningUnitFilter
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import SearchParametersCache
from base.utils.db import convert_order_by_strings_to_expressions
from base.views.learning_units.search.common import SearchTypes


@register.inclusion_tag('templatetags/navigation_learning_unit.html', takes_context=False)
def navigation_learning_unit(user, obj: LearningUnitYear, url_name: str):
    return _navigation_base(_get_learning_unit_filter_class, _reverse_learning_unit_year_url, user, obj, url_name)


@register.inclusion_tag('templatetags/navigation_education_group.html', takes_context=False)
def navigation_education_group(user, obj: EducationGroupYear, url_name: str):
    return _navigation_base(_get_education_group_filter_class, _reverse_education_group_year_url, user, obj, url_name)


def _navigation_base(filter_class_function, reverse_url_function, user, obj, url_name):
    context = {"current_element": obj}
    search_parameters = SearchParametersCache(user, obj.__class__.__name__).cached_data
    if not search_parameters:
        return context

    search_type = search_parameters.get("search_type")
    filter_form_class = filter_class_function(search_type)
    order_by = filter_form_class(data=search_parameters).qs.query.order_by
    order_by_expressions = convert_order_by_strings_to_expressions(order_by) or None
    qs = filter_form_class(data=search_parameters).qs.annotate(
        previous_acronym=Window(
            expression=Lag("acronym"),
            order_by=order_by_expressions,
        ),
        next_acronym=Window(
            expression=Lead("acronym"),
            order_by=order_by_expressions,
        ),
        previous_id=Window(
            expression=Lag("id"),
            order_by=order_by_expressions,
        ),
        next_id=Window(
            expression=Lead("id"),
            order_by=order_by_expressions,
        )
    ).values_list(
        "id",
        "acronym",
        "previous_acronym",
        "previous_id",
        "next_acronym",
        "next_id",
        named=True
    ).order_by(*order_by)

    current_row = _get_current_row(qs, obj)

    if current_row:
        context.update({
            "next_element_title": current_row.next_acronym,
            "next_url": reverse_url_function(current_row.next_id, url_name) if current_row.next_id else None,
            "previous_element_title": current_row.previous_acronym,
            "previous_url": reverse_url_function(current_row.previous_id, url_name) if current_row.previous_id else None
        })
    return context


def _get_education_group_filter_class(search_type):
    return EducationGroupFilter


def _get_learning_unit_filter_class(search_type):
    map_search_type_to_filter_form = {
        SearchTypes.SIMPLE_SEARCH.value: LearningUnitFilter,
        SearchTypes.SERVICE_COURSES_SEARCH.value: ServiceCourseFilter,
        SearchTypes.PROPOSAL_SEARCH.value: ProposalLearningUnitFilter,
        SearchTypes.SUMMARY_LIST.value: LearningUnitDescriptionFicheFilter,
        SearchTypes.BORROWED_COURSE.value: BorrowedLearningUnitSearch,
        SearchTypes.EXTERNAL_SEARCH.value: ExternalLearningUnitFilter,
    }
    return map_search_type_to_filter_form.get(int(search_type) if search_type else None, LearningUnitFilter)


def _get_current_row(qs, obj):
    return next((row for row in qs if row.id == obj.id), None)


def _reverse_education_group_year_url(education_group_year_id, url_name):
    return reverse(url_name, args=[education_group_year_id, education_group_year_id])


def _reverse_learning_unit_year_url(learning_unit_year_id, url_name):
    return reverse(url_name, args=[learning_unit_year_id])


