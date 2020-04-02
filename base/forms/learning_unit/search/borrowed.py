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
import itertools

from django import forms
from django.utils.translation import gettext_lazy as _
from django_filters import filters

from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models import group_element_year, entity_version
from base.models.entity_version import EntityVersion, build_current_entity_version_structure_in_memory
from base.models.enums import entity_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.offer_year_entity import OfferYearEntity
from base.views.learning_units.search.common import SearchTypes


class BorrowedLearningUnitSearch(LearningUnitFilter):
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

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)

        faculty_borrowing_id = None
        faculty_borrowing_acronym = self.form.cleaned_data.get('faculty_borrowing_acronym')
        academic_year = self.form.cleaned_data["academic_year"]

        if faculty_borrowing_acronym:
            try:
                faculty_borrowing_id = EntityVersion.objects.current(academic_year.start_date). \
                    get(acronym__iexact=faculty_borrowing_acronym).entity.id
            except EntityVersion.DoesNotExist:
                return LearningUnitYear.objects.none()

        ids = filter_is_borrowed_learning_unit_year(
            qs,
            academic_year.start_date,
            faculty_borrowing=faculty_borrowing_id
        )
        return qs.filter(id__in=ids)


def filter_is_borrowed_learning_unit_year(learning_unit_year_qs, date, faculty_borrowing=None):
    entities = build_current_entity_version_structure_in_memory(date)
    entities_borrowing_allowed = []
    if faculty_borrowing in entities:
        entities_borrowing_allowed.extend(entities[faculty_borrowing]["all_children"])
        entities_borrowing_allowed.append(entities[faculty_borrowing]["entity_version"])
        entities_borrowing_allowed = [entity_version.entity.id for entity_version in entities_borrowing_allowed]

    entities_faculty = compute_faculty_for_entities(entities)
    map_luy_entity = map_learning_unit_year_with_requirement_entity(learning_unit_year_qs)
    map_luy_education_group_entities = map_learning_unit_year_with_entities_of_education_groups(learning_unit_year_qs)

    ids = []
    for luy in learning_unit_year_qs:
        if _is_borrowed_learning_unit(luy,
                                      entities_faculty,
                                      map_luy_entity,
                                      map_luy_education_group_entities,
                                      entities_borrowing_allowed):
            ids.append(luy.id)

    return ids


def compute_faculty_for_entities(entities):
    faculties_of_entities = {}
    for ev in entities.values():
        faculty = entity_version.get_entity_version_parent_or_itself_from_type(
            entities,
            ev["entity_version"].acronym,
            entity_type.FACULTY
        )
        faculties_of_entities[ev["entity_version"].entity_id] = faculty.id if faculty else None
    return faculties_of_entities


def map_learning_unit_year_with_requirement_entity(learning_unit_year_qs):
    learning_unit_years_with_entity = learning_unit_year_qs \
        .select_related('learning_container_year__requirement_entity') \
        .values_list("id", 'learning_container_year__requirement_entity')
    return {luy_id: entity_id for luy_id, entity_id in learning_unit_years_with_entity}


def map_learning_unit_year_with_entities_of_education_groups(learning_unit_year_qs):
    formations = group_element_year.find_learning_unit_roots(
        learning_unit_year_qs,
        return_result_params={
            'parents_as_instances': False
        }
    )
    education_group_ids = list(itertools.chain.from_iterable(formations.values()))
    offer_year_entity = OfferYearEntity.objects.filter(education_group_year__in=education_group_ids). \
        values_list("education_group_year", "entity")
    dict_entity_of_education_group = {education_group_year_id: entity_id for education_group_year_id, entity_id
                                      in offer_year_entity}

    dict_education_group_year_entities_for_learning_unit_year = {}
    for luy_id, formations_ids in formations.items():
        dict_education_group_year_entities_for_learning_unit_year[luy_id] = \
            [dict_entity_of_education_group.get(formation_id) for formation_id in formations_ids]
    return dict_education_group_year_entities_for_learning_unit_year


def _is_borrowed_learning_unit(luy, map_entity_faculty, map_luy_entity, map_luy_education_group_entities,
                               entities_borrowing_allowed):
    luy_entity = map_luy_entity.get(luy.id)
    luy_faculty = map_entity_faculty.get(luy_entity)

    if luy_faculty is None:
        return False

    def is_entity_allowed(entity):
        return not entities_borrowing_allowed or entity in entities_borrowing_allowed

    entities_allowed = filter(is_entity_allowed, map_luy_education_group_entities.get(luy.id, []))
    for education_group_entity in entities_allowed:
        if luy_faculty != map_entity_faculty.get(education_group_entity) \
                and map_entity_faculty.get(education_group_entity) is not None:
            return True
    return False
