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
from distutils.util import strtobool

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Subquery, Exists, Case, When, Q, Value, CharField
from django.db.models.fields import BLANK_CHOICE_DASH, BooleanField
from django.db.models.functions import Concat
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django_filters import FilterSet, filters

from base import models as mdl
from base.business.education_groups.general_information_sections import MOBILITY
from base.business.entity import get_entities_ids, build_entity_container_prefetch
from base.business.entity_version import SERVICE_COURSE
from base.business.learning_unit import CMS_LABEL_PEDAGOGY
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.common import get_clean_data, treat_empty_or_str_none_as_none, TooManyResultsException
from base.forms.search.search_form import BaseSearchForm
from base.forms.utils.choice_field import add_blank
from base.forms.utils.dynamic_field import DynamicChoiceField
from base.models import learning_unit_year, group_element_year, entity_calendar
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.campus import Campus
from base.models.entity_version import EntityVersion, build_current_entity_version_structure_in_memory
from base.models.enums import entity_container_year_link_type, learning_unit_year_subtypes, active_status, \
    entity_type, learning_container_year_types, quadrimesters
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.learning_unit_year import LearningUnitYear
from base.models.offer_year_entity import OfferYearEntity
from base.models.organization_address import find_distinct_by_country
from base.models.proposal_learning_unit import ProposalLearningUnit
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from reference.models.country import Country


class LearningUnitSearchForm(BaseSearchForm):
    ALL_LABEL = (None, pgettext_lazy("plural", "All"))
    ALL_CHOICES = (ALL_LABEL,)

    MOBILITY = 'mobility'
    MOBILITY_CHOICE = ((MOBILITY, _('Mobility')),)
    _search_mobility = False

    academic_year_id = forms.ModelChoiceField(
        label=_('Ac yr.'),
        queryset=AcademicYear.objects.all(),
        empty_label=pgettext_lazy("plural", "All"),
    )

    requirement_entity_acronym = forms.CharField(
        max_length=20,
        label=_('Req. Entity')
    )

    acronym = forms.CharField(
        max_length=15,
        label=_('Code')
    )

    tutor = forms.CharField(
        max_length=40,
        label=_('Tutor')
    )

    allocation_entity_acronym = forms.CharField(
        max_length=20,
        label=_('Alloc. Ent.')
    )

    quadrimester = forms.ChoiceField(
        label=_('Quadri'),
        choices=ALL_CHOICES + quadrimesters.LEARNING_UNIT_YEAR_QUADRIMESTERS
    )

    with_entity_subordinated = forms.BooleanField(label=_('Include subordinate entities'))

    def get_queryset(self):
        """ Filter a LearningUnitYearQueryset """
        has_proposal = ProposalLearningUnit.objects.filter(
            learning_unit_year=OuterRef('pk'),
        )
        entity_requirement = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__requirement_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        entity_allocation = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__allocation_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        queryset = mdl.learning_unit_year.search(**self.cleaned_data)

        queryset = self._filter_external_learning_units(queryset)

        queryset = queryset.select_related(
            'academic_year', 'learning_container_year__academic_year',
            'language', 'proposallearningunit', 'externallearningunityear'
        ).order_by('academic_year__year', 'acronym').annotate(
            has_proposal=Exists(has_proposal),
            entity_requirement=Subquery(entity_requirement),
            entity_allocation=Subquery(entity_allocation),
        )
        queryset = self.get_filter_learning_container_ids(queryset)

        return queryset

    def clean_container_type(self):
        container_type = self.cleaned_data['container_type']
        if container_type == LearningUnitSearchForm.MOBILITY:
            self._search_mobility = True
            return learning_container_year_types.EXTERNAL
        return container_type

    def _filter_external_learning_units(self, qs):
        container_type = self.cleaned_data.get('container_type')
        if container_type:
            if self._search_mobility:
                qs = qs.filter(externallearningunityear__mobility=True)
            elif container_type == learning_container_year_types.EXTERNAL:
                qs = qs.filter(externallearningunityear__co_graduation=True)
        return qs

    def get_filter_learning_container_ids(self, qs):
        """
        Append a filter on the queryset if entities are given in the search

        :param qs: LearningUnitYearQuerySet
        :return: queryset
        """
        requirement_entity_acronym = self.cleaned_data.get('requirement_entity_acronym')
        allocation_entity_acronym = self.cleaned_data.get('allocation_entity_acronym')
        with_entity_subordinated = self.cleaned_data.get('with_entity_subordinated', False)

        if requirement_entity_acronym:
            requirement_entity_ids = get_entities_ids(requirement_entity_acronym, with_entity_subordinated)

            qs = qs.filter(
                learning_container_year__requirement_entity__in=requirement_entity_ids,
            )

        if allocation_entity_acronym:
            allocation_entity_ids = get_entities_ids(allocation_entity_acronym, with_entity_subordinated)

            qs = qs.filter(
                learning_container_year__allocation_entity__in=allocation_entity_ids,
            )

        return qs


class LearningUnitYearForm(LearningUnitSearchForm):
    MAX_RECORDS = 2000
    container_type = forms.ChoiceField(
        label=_('Type'),
        choices=LearningUnitSearchForm.ALL_CHOICES + LearningContainerYearType.choices()
        + LearningUnitSearchForm.MOBILITY_CHOICE,
    )

    subtype = forms.ChoiceField(
        label=_('Subtype'),
        choices=LearningUnitSearchForm.ALL_CHOICES + learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
    )

    status = forms.ChoiceField(
        label=_('Status'),
        choices=LearningUnitSearchForm.ALL_CHOICES + active_status.ACTIVE_STATUS_LIST[:-1],
    )

    title = forms.CharField(
        max_length=20,
        label=_('Title')
    )

    allocation_entity_acronym = forms.CharField(
        max_length=20,
        label=_('Alloc. Ent.')
    )

    faculty_borrowing_acronym = forms.CharField(
        max_length=20,
        label=_("Faculty borrowing")
    )

    def __init__(self, *args, **kwargs):
        self.service_course_search = kwargs.pop('service_course_search', False)
        self.borrowed_course_search = kwargs.pop('borrowed_course_search', False)

        super().__init__(*args, **kwargs)

        if self.borrowed_course_search:
            self.fields["academic_year_id"].empty_label = None

        self.fields["with_entity_subordinated"].initial = True

    def clean_acronym(self):
        acronym = self.cleaned_data.get('acronym')
        acronym = treat_empty_or_str_none_as_none(acronym)
        if acronym and not learning_unit_year.check_if_acronym_regex_is_valid(acronym):
            raise ValidationError(_('LU_ERRORS_INVALID_REGEX_SYNTAX'))
        return acronym

    def clean_faculty_borrowing_acronym(self):
        data_cleaned = self.cleaned_data.get('faculty_borrowing_acronym')
        if data_cleaned:
            return data_cleaned.upper()

    def clean(self):
        return get_clean_data(self.cleaned_data)

    def get_activity_learning_units(self):
        if self.service_course_search:
            return self._get_service_course_learning_units()
        elif self.borrowed_course_search:
            return self.get_learning_units()
        else:
            # Simple search
            return self.get_queryset()

    def _get_service_course_learning_units(self):
        learning_units = self.get_learning_units(service_course_search=True)
        # FIXME Ugly method to keep a queryset, we must simplify the db structure to easily fetch the service course
        return learning_units.filter(pk__in=[
            lu.pk for lu in learning_units if lu.entities.get(SERVICE_COURSE)
        ])

    def get_learning_units(self, service_course_search=None):
        service_course_search = service_course_search or self.service_course_search

        learning_units = self.get_queryset()

        # FIXME: use one queryset for service cource search and borrowed course search instead of filtering in python
        if not service_course_search and not self.borrowed_course_search \
                and self.cleaned_data and learning_units.count() > self.MAX_RECORDS:
            raise TooManyResultsException

        if self.borrowed_course_search:
            learning_units = self._filter_borrowed_learning_units(learning_units)

        learning_units = learning_units.prefetch_related(
            build_entity_container_prefetch(entity_container_year_link_type.ALLOCATION_ENTITY),
            build_entity_container_prefetch(entity_container_year_link_type.REQUIREMENT_ENTITY),
        )
        for learning_unit in learning_units:
            append_latest_entities(learning_unit, service_course_search)

        return learning_units

    def _filter_borrowed_learning_units(self, qs_learning_units):
        faculty_borrowing_id = None
        faculty_borrowing_acronym = self.cleaned_data.get('faculty_borrowing_acronym')
        academic_year = self.cleaned_data["academic_year_id"]

        if faculty_borrowing_acronym:
            try:
                faculty_borrowing_id = EntityVersion.objects.current(academic_year.start_date). \
                    get(acronym=faculty_borrowing_acronym).entity.id
            except EntityVersion.DoesNotExist:
                return LearningUnitYear.objects.none()

        ids = filter_is_borrowed_learning_unit_year(
            qs_learning_units,
            academic_year.start_date,
            faculty_borrowing=faculty_borrowing_id
        )
        return self.get_queryset().filter(id__in=ids)


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
    learning_unit_years_with_entity = learning_unit_year_qs\
        .select_related('learning_container_year__requirement_entity')\
        .values_list("id", 'learning_container_year__requirement_entity')
    return {luy_id: entity_id for luy_id, entity_id in learning_unit_years_with_entity}


def map_learning_unit_year_with_entities_of_education_groups(learning_unit_year_qs):
    formations = group_element_year.find_learning_unit_formations(learning_unit_year_qs, parents_as_instances=False)
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
        return not entities_borrowing_allowed or map_entity_faculty.get(entity) in entities_borrowing_allowed

    entities_allowed = filter(is_entity_allowed, map_luy_education_group_entities.get(luy.id, []))
    for education_group_entity in entities_allowed:
        if luy_faculty != map_entity_faculty.get(education_group_entity) \
                and map_entity_faculty.get(education_group_entity) is not None:
            return True
    return False


class ExternalLearningUnitYearForm(LearningUnitYearForm):
    country = forms.ModelChoiceField(
        queryset=Country.objects.filter(organizationaddress__isnull=False).distinct().order_by('name'),
        required=False, label=_("Country")
    )
    campus = DynamicChoiceField(choices=BLANK_CHOICE_DASH, required=False, label=_("Institution"),
                                help_text=_("Please select a country and a city first"))
    city = DynamicChoiceField(choices=BLANK_CHOICE_DASH, required=False, label=_("City"),
                              help_text=_("Please select a country first"))

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

    def get_queryset(self):
        learning_units = super().get_queryset().filter(
            externallearningunityear__co_graduation=True,
            externallearningunityear__mobility=False,
        ).select_related(
            'campus__organization'
        )
        return learning_units


class LearningUnitDescriptionFicheFilter(FilterSet):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=True,
        label=_('Ac yr.')
    )
    acronym = filters.CharFilter(
        field_name="acronym",
        lookup_expr='icontains',
        max_length=40,
        required=False,
        label=_('Code'),
    )
    learning_unit_title = filters.CharFilter(
        field_name='full_title',
        lookup_expr='icontains',
        label=_('Title'),
    )
    container_type = filters.ChoiceFilter(
        field_name='learning_container_year__container_type',
        choices=LearningContainerYearType.choices() + ((MOBILITY, _('Mobility')),),
        label=_('Type'),
        empty_label=pgettext_lazy("plural", "All")
    )
    subtype = filters.ChoiceFilter(
        choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        label=_('Subtype'),
        empty_label=pgettext_lazy("plural", "All")
    )
    status = filters.TypedChoiceFilter(
        choices=(('', _("All")), ('true', _("Active")), ('false', _("Inactive"))),
        label=_('Status'),
        coerce=strtobool,
    )
    quadrimester = filters.ChoiceFilter(
        choices=quadrimesters.LEARNING_UNIT_YEAR_QUADRIMESTERS,
        label=_('Quadri'),
        empty_label=pgettext_lazy("plural", "All")
    )
    tutor = filters.CharFilter(
        method='filter_tutor',
        label=_('Tutor'),
    )
    requirement_entity = filters.CharFilter(
        method='filter_requirement_entity_with_entity_subordinated',
        label=_('Req. Entity')
    )
    allocation_entity = filters.CharFilter(
        method='filter_allocation_entity_with_entity_subordinated',
        label=_('Alloc. Ent.')
    )
    with_entity_subordinated = filters.BooleanFilter(
        method=lambda queryset, *args, **kwargs: queryset,
        label=_('Include subordinate entities'),
        widget=forms.CheckboxInput
    )

    class Meta:
        model = LearningUnitYear
        fields = []

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        translated_text_qs = TranslatedText.objects.filter(
            entity=LEARNING_UNIT_YEAR,
            text_label__label__in=CMS_LABEL_PEDAGOGY,
            changed__isnull=False,
            reference=OuterRef('pk')
        ).order_by("-changed")

        queryset = LearningUnitYear.objects.all().annotate(
            full_title=Case(
                When(
                    Q(learning_container_year__common_title__isnull=True) |
                    Q(learning_container_year__common_title__exact=''),
                    then='specific_title'
                ),
                When(
                    Q(specific_title__isnull=True) | Q(specific_title__exact=''),
                    then='learning_container_year__common_title'
                ),
                default=Concat('learning_container_year__common_title', Value(' - '), 'specific_title'),
                output_field=CharField(),
            ),
            last_translated_text_changed=Subquery(translated_text_qs.values('changed')[:1]),
        )
        super(LearningUnitDescriptionFicheFilter, self).__init__(
            data=data,
            queryset=queryset,
            request=request,
            prefix=prefix,
        )
        self.form.fields['academic_year'].initial = starting_academic_year()
        self.form.fields['with_entity_subordinated'].initial = True

    def filter_tutor(self, queryset, name, value):
        return queryset.filter(
            Q(learningcomponentyear__attributionchargenew__attribution__tutor__person__first_name__icontains=value)
            | Q(learningcomponentyear__attributionchargenew__attribution__tutor__person__last_name__icontains=value)
        )

    def filter_requirement_entity_with_entity_subordinated(self, queryset, name, value):
        with_subordinated = self.form.cleaned_data['with_entity_subordinated']
        if value:
            entity_ids = get_entities_ids(value, with_subordinated)
            queryset = queryset.filter(learning_container_year__requirement_entity__in=entity_ids)
        return queryset

    def filter_allocation_entity_with_entity_subordinated(self, queryset, name, value):
        with_subordinated = self.form.cleaned_data['with_entity_subordinated']
        if value:
            entity_ids = get_entities_ids(value, with_subordinated)
            queryset = queryset.filter(learning_container_year__allocation_entity__in=entity_ids)
        return queryset

    @property
    def qs(self):
        queryset = super(LearningUnitDescriptionFicheFilter, self).qs
        if self.is_bound:
            queryset = self._compute_summary_status(queryset)
            queryset = queryset.select_related('learning_container_year__academic_year', 'academic_year')
        return queryset

    def _compute_summary_status(self, queryset):
        """
        This function will compute the summary status. First, we will take the entity calendar
        (or entity calendar parent and so one) of the requirement entity. If not found, the summary status is
        computed with the general Academic Calendar Object
        """
        entity_calendars_computed = entity_calendar.build_calendar_by_entities(
            self.form.cleaned_data['academic_year'].past(),
            SUMMARY_COURSE_SUBMISSION,
        )
        requirement_entities_ids = queryset.values_list('learning_container_year__requirement_entity', flat=True)

        summary_status_case_statment = [When(last_translated_text_changed__isnull=True, then=False)]
        for requirement_entity_id in set(requirement_entities_ids):
            start_summary_course_submission = entity_calendars_computed.get(requirement_entity_id, {}).get('start_date')
            if start_summary_course_submission is None:
                continue

            summary_status_case_statment.append(
                When(
                    learning_container_year__requirement_entity=requirement_entity_id,
                    last_translated_text_changed__gte=start_summary_course_submission,
                    then=True
                )
            )

        queryset = queryset.annotate(
            summary_status=Case(
                *summary_status_case_statment,
                default=Value(False),
                output_field=BooleanField()
            )
        )
        return queryset
