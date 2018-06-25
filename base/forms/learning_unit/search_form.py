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

import itertools

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Subquery
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.entity import get_entities_ids, get_entity_container_list, build_entity_container_prefetch
from base.business.entity_version import SERVICE_COURSE
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.common import get_clean_data, treat_empty_or_str_none_as_none, TooManyResultsException
from base.forms.search.search_form import BaseSearchForm
from base.forms.utils.choice_field import add_blank
from base.forms.utils.dynamic_field import DynamicChoiceField
from base.forms.utils.uppercase import convert_to_uppercase
from base.models import learning_unit_year, group_element_year
from base.models.academic_year import AcademicYear, current_academic_year
from base.models.campus import Campus
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import EntityVersion, build_current_entity_version_structure_in_memory
from base.models.enums import entity_container_year_link_type, learning_container_year_types, \
    learning_unit_year_subtypes, active_status, entity_type
from base.models.learning_unit_year import convert_status_bool
from base.models.offer_year_entity import OfferYearEntity
from base.models.organization_address import find_distinct_by_country
from reference.models.country import Country

MAX_RECORDS = 1000


class LearningUnitSearchForm(BaseSearchForm):
    MAX_RECORDS = 1000
    ALL_LABEL = (None, _('all_label'))
    ALL_CHOICES = (ALL_LABEL,)

    academic_year_id = forms.ModelChoiceField(
        label=_('academic_year_small'),
        queryset=AcademicYear.objects.all(),
        empty_label=_('all_label'),
    )

    requirement_entity_acronym = forms.CharField(
        max_length=20,
        label=_('requirement_entity_small')
    )

    acronym = forms.CharField(
        max_length=15,
        label=_('code')
    )

    tutor = forms.CharField(
        max_length=40,
        label=_('tutor')
    )

    summary_responsible = forms.CharField(
        max_length=20,
        label=_('summary_responsible')
    )

    allocation_entity_acronym = forms.CharField(
        max_length=20,
        label=_('allocation_entity_small')
    )

    with_entity_subordinated = forms.BooleanField(label=_('with_entity_subordinated_small'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year_id'].initial = current_academic_year()

    def clean_requirement_entity_acronym(self):
        return convert_to_uppercase(self.cleaned_data.get('requirement_entity_acronym'))

    def clean_allocation_entity_acronym(self):
        return convert_to_uppercase(self.cleaned_data.get('allocation_entity_acronym'))


class LearningUnitYearForm(LearningUnitSearchForm):
    container_type = forms.ChoiceField(
        label=_('type'),
        choices=LearningUnitSearchForm.ALL_CHOICES + learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES,
    )

    subtype = forms.ChoiceField(
        label=_('subtype'),
        choices=LearningUnitSearchForm.ALL_CHOICES + learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
    )

    status = forms.ChoiceField(
        label=_('status'),
        choices=LearningUnitSearchForm.ALL_CHOICES + active_status.ACTIVE_STATUS_LIST[:-1],
    )

    title = forms.CharField(
        max_length=20,
        label=_('title')
    )

    allocation_entity_acronym = forms.CharField(
        max_length=20,
        label=_('allocation_entity_small')
    )

    faculty_borrowing_acronym = forms.CharField(
        max_length=20,
        label=_("faculty_borrowing")
    )

    def __init__(self, *args, **kwargs):
        self.service_course_search = kwargs.pop('service_course_search', False)
        self.borrowed_course_search = kwargs.pop('borrowed_course_search', False)
        super().__init__(*args, **kwargs)

        if self.borrowed_course_search:
            self.fields["with_entity_subordinated"].initial = True
            self.fields["academic_year_id"].required = True
            self.fields["academic_year_id"].empty_label = None

    def clean_acronym(self):
        acronym = self.cleaned_data.get('acronym')
        acronym = treat_empty_or_str_none_as_none(acronym)
        if acronym and not learning_unit_year.check_if_acronym_regex_is_valid(acronym):
            raise ValidationError(_('LU_ERRORS_INVALID_REGEX_SYNTAX'))
        return acronym

    def clean_allocation_entity_acronym(self):
        return convert_to_uppercase(self.cleaned_data.get('allocation_entity_acronym'))

    def clean_faculty_borrowing_acronym(self):
        return convert_to_uppercase(self.cleaned_data.get('faculty_borrowing_acronym'))

    def clean(self):
        return get_clean_data(self.cleaned_data)

    def get_activity_learning_units(self):
        return self._get_service_course_learning_units() if self.service_course_search else self.get_learning_units()

    def _get_service_course_learning_units(self):
        learning_units = self.get_learning_units(service_course_search=True)
        return [lu for lu in learning_units if lu.entities.get(SERVICE_COURSE)]

    def get_learning_units(self, service_course_search=None, requirement_entities=None, luy_status=None):
        service_course_search = service_course_search or self.service_course_search
        search_criterias = self.cleaned_data.copy()
        search_criterias['status'] = self._set_status(luy_status)

        if requirement_entities:
            search_criterias['requirement_entities'] = requirement_entities

        # TODO Use a queryset instead !!
        search_criterias['learning_container_year_id'] = get_filter_learning_container_ids(search_criterias)

        if not service_course_search \
                and search_criterias \
                and mdl.learning_unit_year.count_search_results(**search_criterias) > self.MAX_RECORDS:
            raise TooManyResultsException

        learning_units = mdl.learning_unit_year.search(**search_criterias) \
            .select_related('academic_year', 'learning_container_year', 'learning_container_year__academic_year') \
            .prefetch_related(build_entity_container_prefetch()) \
            .order_by('academic_year__year', 'acronym')

        if self.borrowed_course_search:
            learning_units = self._filter_borrowed_learning_units(learning_units)

        # FIXME We must keep a queryset
        return [append_latest_entities(learning_unit, service_course_search) for learning_unit in learning_units]

    def _set_status(self, luy_status):
        return convert_status_bool(luy_status) if luy_status else self.cleaned_data['status']

    def _filter_borrowed_learning_units(self, learning_units):
        faculty_borrowing_id = None
        if self.cleaned_data["faculty_borrowing_acronym"]:
            try:
                faculty_borrowing_id = EntityVersion.objects.current(self.cleaned_data["academic_year_id"].start_date).\
                    get(acronym=self.cleaned_data["faculty_borrowing_acronym"]).entity.id
            except EntityVersion.DoesNotExist:
                return []
        return filter_is_borrowed_learning_unit_year(learning_units, self.cleaned_data["academic_year_id"].start_date,
                                                     faculty_borrowing=faculty_borrowing_id)


def get_filter_learning_container_ids(filter_data):
    requirement_entity_acronym = filter_data.get('requirement_entity_acronym')
    allocation_entity_acronym = filter_data.get('allocation_entity_acronym')
    with_entity_subordinated = filter_data.get('with_entity_subordinated', False)
    entities_id_list_requirement = []
    entities_id_list_allocation = []

    if requirement_entity_acronym:
        entity_ids = get_entities_ids(requirement_entity_acronym, with_entity_subordinated)
        entities_id_list_requirement += get_entity_container_list(entity_ids,
                                                                  entity_container_year_link_type.REQUIREMENT_ENTITY)

    if allocation_entity_acronym:
        entity_ids = get_entities_ids(allocation_entity_acronym, with_entity_subordinated)
        entities_id_list_allocation += get_entity_container_list(entity_ids,
                                                                 entity_container_year_link_type.ALLOCATION_ENTITY)

    if requirement_entity_acronym and allocation_entity_acronym:
        return _get_common_entities(entities_id_list_allocation, entities_id_list_requirement)
    else:
        return _get_entity_ids_list(allocation_entity_acronym, entities_id_list_allocation,
                                    entities_id_list_requirement, requirement_entity_acronym)


def _get_common_entities(entities_id_list_allocation, entities_id_list_requirement):
    return list(set(entities_id_list_allocation).intersection(set(entities_id_list_requirement)))


def filter_is_borrowed_learning_unit_year(learning_unit_year_qs, date, faculty_borrowing=None):
    entities = build_current_entity_version_structure_in_memory(date)
    entities_borrowing_allowed = []
    if faculty_borrowing in entities:
        entities_borrowing_allowed.extend(entities[faculty_borrowing]["all_children"])
        entities_borrowing_allowed.append(entities[faculty_borrowing]["entity_version"])
        entities_borrowing_allowed = [entity_version.entity.id for entity_version in entities_borrowing_allowed]
    entities_faculty = compute_faculty_for_entities(entities)
    map_luy_entity = map_learning_unit_year_with_requirement_entity(learning_unit_year_qs)
    map_luy_education_group_entities = \
        map_learning_unit_year_with_entities_of_education_groups(learning_unit_year_qs)

    return filter(lambda luy: __is_borrowed_learning_unit(luy, entities_faculty, map_luy_entity,
                                                          map_luy_education_group_entities, entities_borrowing_allowed),
                  learning_unit_year_qs)


def compute_faculty_for_entities(entities):
    return {entity_id: __search_faculty_for_entity(entity_id, entities) for entity_id in entities.keys()}


def __search_faculty_for_entity(entity_id, entities):
    entity_data = entities[entity_id]
    if entity_data["entity_version"].entity_type == entity_type.FACULTY:
        return entity_id

    entity_version_parent = entity_data["entity_version_parent"]
    if entity_version_parent is None or entity_version_parent.entity.id not in entities:
        return entity_id

    new_current = entity_version_parent.entity.id
    return __search_faculty_for_entity(new_current, entities)


def map_learning_unit_year_with_requirement_entity(learning_unit_year_qs):
    entity_container_years = EntityContainerYear.objects.\
        filter(learning_container_year__pk=OuterRef("learning_container_year__pk"),
               type=entity_container_year_link_type.REQUIREMENT_ENTITY)
    learning_unit_years_with_entity = learning_unit_year_qs.values_list("id").\
        annotate(entity=Subquery(entity_container_years.values("entity")))
    return {luy_id: entity_id for luy_id, entity_id in learning_unit_years_with_entity}


def map_learning_unit_year_with_entities_of_education_groups(learning_unit_year_qs):
    formations = group_element_year.find_learning_unit_formations(learning_unit_year_qs, parents_as_instances=False)
    education_group_ids = list(itertools.chain.from_iterable(formations.values()))
    offer_year_entity = OfferYearEntity.objects.filter(education_group_year__in=education_group_ids).\
        values_list("education_group_year", "entity")
    dict_entity_of_education_group = {education_group_year_id: entity_id for education_group_year_id, entity_id
                                      in offer_year_entity}

    dict_education_group_year_entities_for_learning_unit_year = {}
    for luy_id, formations_ids in formations.items():
        dict_education_group_year_entities_for_learning_unit_year[luy_id] = \
            [dict_entity_of_education_group.get(formation_id) for formation_id in formations_ids]
    return dict_education_group_year_entities_for_learning_unit_year


def __is_borrowed_learning_unit(luy, map_entity_faculty, map_luy_entity, map_luy_education_group_entities,
                                entities_borrowing_allowed):
    luy_entity = map_luy_entity.get(luy.id)
    luy_faculty = map_entity_faculty.get(luy_entity)

    if luy_faculty is None:
        return False

    def is_entity_allowed(entity):
        return not entities_borrowing_allowed or map_entity_faculty.get(entity) in entities_borrowing_allowed

    entities_allowed = filter(is_entity_allowed, map_luy_education_group_entities.get(luy.id, []))
    for education_group_entity in entities_allowed:
        if luy_faculty != map_entity_faculty.get(education_group_entity) \
                and map_entity_faculty.get(education_group_entity) is not None:
            return True
    return False


def _get_entity_ids_list(allocation_entity_acronym, entities_id_list_allocation, entities_id_list_requirement,
                         requirement_entity_acronym):
    if requirement_entity_acronym:
        return entities_id_list_requirement
    elif allocation_entity_acronym:
        return entities_id_list_allocation
    else:
        return None


class ExternalLearningUnitYearForm(LearningUnitYearForm):
    country = forms.ModelChoiceField(queryset=Country.objects.filter(organizationaddress__isnull=False)
                                     .distinct().order_by('name'),
                                     required=False, label=_("country"))
    campus = DynamicChoiceField(choices=BLANK_CHOICE_DASH, required=False, label=_("institution"))
    city = DynamicChoiceField(choices=BLANK_CHOICE_DASH, required=False, label=_("city"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get('country'):
            self._init_dropdown_list()

    def _init_dropdown_list(self):
        if self.data.get('city', None):
            self._get_cities()
        if self.data.get('campus', None):
            self._get_campus_list()

    def _get_campus_list(self):
        campus_list = Campus.objects.filter(
            organization__organizationaddress__city=self.data['city']
        ).distinct('organization__name').order_by('organization__name').values('pk', 'organization__name')
        campus_choice_list = []
        for a_campus in campus_list:
            campus_choice_list.append(((a_campus['pk']), (a_campus['organization__name'])))
        self.fields['campus'].choices = add_blank(campus_choice_list)

    def _get_cities(self):
        cities = find_distinct_by_country(self.data['country'])
        cities_choice_list = []
        for a_city in cities:
            city_name = a_city['city']
            cities_choice_list.append(tuple((city_name, city_name)))

        self.fields['city'].choices = add_blank(cities_choice_list)

    def get_learning_units(self):
        clean_data = self.cleaned_data
        learning_units = mdl.external_learning_unit_year.search(
            academic_year_id=clean_data['academic_year_id'],
            acronym=clean_data['acronym'],
            title=clean_data['title'],
            country=clean_data['country'],
            city=clean_data['city'],
            campus=clean_data['campus']
        ).select_related('learning_unit_year__academic_year', ) \
            .order_by('learning_unit_year__academic_year__year', 'learning_unit_year__acronym')

        return learning_units

    def clean_city(self):
        return _get_value(self.cleaned_data.get('city'))

    def clean_country(self):
        return _get_value(self.cleaned_data.get('country'))

    def clean_campus(self):
        return _get_value(self.cleaned_data.get('campus'))

    def clean(self):
        if not self._has_criteria():
            self.add_error(None, _('minimum_one_criteria'))


def _get_value(data_cleaned):
    if data_cleaned == BLANK_CHOICE_DASH[0][1]:
        return None
    return data_cleaned
