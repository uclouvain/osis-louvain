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
from django import forms
from django.db.models import Q, OuterRef, Exists
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import FilterSet, filters, OrderingFilter

from base.business.entity import get_entities_ids
from base.forms.utils.filter_field import filter_field_by_regex
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.enums import quadrimesters, learning_unit_year_subtypes, active_status, learning_container_year_types
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.learning_units.search.common import SearchTypes

MOBILITY = 'mobility'
MOBILITY_CHOICE = ((MOBILITY, _('Mobility')),)


class LearningUnitFilter(FilterSet):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=False,
        label=_('Ac yr.'),
        empty_label=pgettext_lazy("plural", "All"),
    )
    acronym = filters.CharFilter(
        field_name="acronym",
        lookup_expr="iregex",
        max_length=40,
        required=False,
        label=_('Code'),
    )
    requirement_entity = filters.CharFilter(
        method='filter_entity',
        max_length=20,
        label=_('Req. Entity'),
    )
    allocation_entity = filters.CharFilter(
        method='filter_entity',
        max_length=20,
        label=_('Alloc. Entity'),
    )
    with_entity_subordinated = filters.BooleanFilter(
        method=lambda queryset, *args, **kwargs: queryset,
        label=_('Include subordinate entities'),
        widget=forms.CheckboxInput,
        initial='True'
    )
    tutor = filters.CharFilter(
        method="filter_tutor",
        max_length=40,
        label=_('Tutor'),
    )
    quadrimester = filters.ChoiceFilter(
        choices=quadrimesters.LearningUnitYearQuadrimester.choices(),
        required=False,
        field_name="quadrimester",
        label=_('Quadri'),
        empty_label=pgettext_lazy("plural", "All"),
    )

    container_type = filters.ChoiceFilter(
        choices=LearningContainerYearType.choices() + MOBILITY_CHOICE,
        required=False,
        field_name="learning_container_year__container_type",
        label=_('Type'),
        empty_label=pgettext_lazy("plural", "All"),
        method="filter_container_type"
    )
    subtype = filters.ChoiceFilter(
        choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        required=False,
        field_name="subtype",
        label=_('Subtype'),
        empty_label=pgettext_lazy("plural", "All")
    )
    status = filters.ChoiceFilter(
        choices=active_status.ACTIVE_STATUS_LIST_FOR_FILTER,
        required=False,
        label=_('Status'),
        field_name="status",
        empty_label=pgettext_lazy("plural", "All")
    )
    title = filters.CharFilter(
        field_name="full_title",
        method="filter_learning_unit_year_field",
        max_length=40,
        label=_('Title'),
    )
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.SIMPLE_SEARCH.value
    )

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('academic_year__year', 'academic_year'),
            ('acronym', 'acronym'),
            ('full_title', 'title'),
            ('learning_container_year__container_type', 'type'),
            ('subtype', 'subtype'),
            ('entity_requirement', 'requirement_entity'),
            ('entity_allocation', 'allocation_entity'),
            ('credits', 'credits'),
            ('status', 'status'),
            ('has_proposal', 'has_proposal'),
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = LearningUnitYear
        fields = [
            "academic_year",
            "acronym",
            "title",
            "container_type",
            "subtype",
            "requirement_entity",
            "allocation_entity",
            "credits",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        self.form.fields["academic_year"].initial = starting_academic_year()

    def filter_tutor(self, queryset, name, value):
        for tutor_name in value.split():
            queryset = queryset.filter(
                Q(learningcomponentyear__attributionchargenew__attribution__tutor__person__first_name__iregex=tutor_name
                  ) |
                Q(learningcomponentyear__attributionchargenew__attribution__tutor__person__last_name__iregex=tutor_name)
            ).distinct()
        return queryset

    def filter_container_type(self, queryset, name, value):
        if value == MOBILITY:
            return queryset.filter(externallearningunityear__mobility=True)
        elif value == learning_container_year_types.EXTERNAL:
            return queryset.filter(externallearningunityear__co_graduation=True)
        return queryset.filter(learning_container_year__container_type=value)

    def filter_entity(self, queryset, name, value):
        return filter_by_entities(name, queryset, value, self.form.cleaned_data['with_entity_subordinated'])

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return LearningUnitYear.objects.none()

        has_proposal = ProposalLearningUnit.objects.filter(
            learning_unit_year=OuterRef('pk'),
        )

        queryset = LearningUnitYear.objects_with_container.select_related(
            'academic_year',
            'learning_container_year__academic_year',
            'language',
            'proposallearningunit',
            'externallearningunityear'
        ).order_by('academic_year__year', 'acronym').annotate(
            has_proposal=Exists(has_proposal),
        )
        queryset = LearningUnitYearQuerySet.annotate_full_title_class_method(queryset)
        queryset = LearningUnitYearQuerySet.annotate_entities_allocation_and_requirement_acronym(queryset)
        return queryset

    def filter_learning_unit_year_field(self, queryset, name, value):
        return filter_field_by_regex(queryset, name, value)


def filter_by_entities(name, queryset, value, with_subordinated):
    lookup_expression = "__".join(["learning_container_year", name, "in"])
    if value:
        entity_ids = get_entities_ids(value, with_subordinated)
        queryset = queryset.filter(**{lookup_expression: entity_ids})
    return queryset
