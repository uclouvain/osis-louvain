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
from collections import defaultdict
from typing import Dict, List

from django import forms
from django.utils.translation import gettext_lazy as _
from django_filters import filters

from base.business.entity_version import load_main_entity_structure, MainEntityStructure
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from base.views.learning_units.search.common import SearchTypes
from program_management.ddd.repositories.find_roots import find_roots_for_element_ids
from program_management.models.element import Element


class BorrowedLearningUnitSearch(LearningUnitFilter):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=True,
        label=_('Ac yr.'),
        empty_label=None
    )
    faculty_borrowing_acronym = filters.CharFilter(
        method=lambda queryset, *args, **kwargs: queryset,
        max_length=20,
        label=_("Faculty borrowing")
    )
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.BORROWED_COURSE.value
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields["academic_year"].required = True

    def filter_queryset(self, queryset: 'LearningUnitYearQuerySet'):
        qs = super().filter_queryset(queryset).select_related("element").exclude(element__isnull=True)

        faculty_borrowing_id = None
        faculty_borrowing_acronym = self.form.cleaned_data.get('faculty_borrowing_acronym')
        academic_year = self.form.cleaned_data["academic_year"]

        if faculty_borrowing_acronym:
            try:
                faculty_borrowing_id = EntityVersion.objects.current(academic_year.start_date). \
                    get(acronym__iexact=faculty_borrowing_acronym).entity.id
            except EntityVersion.DoesNotExist:
                return LearningUnitYear.objects.none()

        ids = filter_borrowed_learning_units(
            qs,
            faculty_borrowing_id=faculty_borrowing_id
        )
        return qs.filter(id__in=ids)


def filter_borrowed_learning_units(
        learning_unit_year_qs: LearningUnitYearQuerySet,
        faculty_borrowing_id: int = None
):
    entity_structure = load_main_entity_structure()
    entities_borrowing_restriction = _get_faculty_entities(entity_structure, faculty_borrowing_id) \
        if faculty_borrowing_id else []

    map_element_entities = _get_management_entity_of_roots_by_elements(
        [luy.element.id for luy in learning_unit_year_qs],
        entities_borrowing_restriction,
    )

    return [luy.id for luy in learning_unit_year_qs
            if _is_borrowed_course(luy, map_element_entities.get(luy.element.id, []), entity_structure)]


def _get_faculty_entities(entity_structure: 'MainEntityStructure', faculty_borrowing_id: int) -> List[int]:
    children = entity_structure.get_children(faculty_borrowing_id)
    return [faculty_borrowing_id] + [child.entity_id for child in children]


def _get_management_entity_of_roots_by_elements(
        element_ids: List[int],
        entities_restricted: List[int]
) -> Dict[int, List[int]]:
    root_child_lists = find_roots_for_element_ids(element_ids)
    root_element_ids = [list_element["root_id"] for list_element in root_child_lists]

    root_element_qs = Element.objects.filter(id__in=root_element_ids)
    if entities_restricted:
        root_element_qs = root_element_qs.filter(group_year__management_entity_id__in=entities_restricted)
    dict_entity_of_element_id = dict(root_element_qs.values_list("id", "group_year__management_entity"))

    dict_group_year_entities_for_learning_unit_year = defaultdict(list)
    for list_element in root_child_lists:
        if dict_entity_of_element_id.get(list_element["root_id"]):
            dict_group_year_entities_for_learning_unit_year[list_element["child_id"]].append(
                dict_entity_of_element_id.get(list_element["root_id"])
            )
    return dict_group_year_entities_for_learning_unit_year


def _is_borrowed_course(
        luy: 'LearningUnitYearQuerySet',
        entities_using_luy: List[int],
        entity_structure: 'MainEntityStructure') -> bool:
    for entity in entities_using_luy:
        if not entity_structure.in_same_faculty(luy.learning_container_year.requirement_entity_id, entity):
            return True
    return False
