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
from django.db.models import Q, OuterRef, Subquery, Exists
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import FilterSet, filters, OrderingFilter

from base.business import event_perms
from base.business.entity import get_entities_ids
from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.proposal_state import ProposalState, LimitedProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.learning_units.search.common import SearchTypes


def _get_sorted_choices(tuple_of_choices):
    return tuple(sorted(tuple_of_choices, key=lambda item: item[1]))


class ProposalLearningUnitOrderingFilter(OrderingFilter):
    def filter(self, qs, value):
        queryset = super().filter(qs, value)
        if value and 'folder' in value:
            queryset = queryset.order_by("entity_folder", "proposallearningunit__folder_id")
        elif value and '-folder' in value:
            queryset = queryset.order_by("-entity_folder", "-proposallearningunit__folder_id")
        return queryset


class ProposalLearningUnitFilter(FilterSet):
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
    entity_folder = filters.ChoiceFilter(
        field_name="proposallearningunit__entity_id",
        label=_('Folder entity'),
        required=False,
        empty_label=pgettext_lazy("plural", "All"),
    )
    folder = filters.NumberFilter(
        field_name="proposallearningunit__folder_id",
        min_value=0,
        required=False,
        label=_('Folder num.'),
        widget=forms.TextInput()
    )
    proposal_type = filters.ChoiceFilter(
        field_name="proposallearningunit__type",
        label=_('Proposal type'),
        choices=_get_sorted_choices(ProposalType.choices()),
        required=False,
        empty_label=pgettext_lazy("plural", "All"),
    )
    proposal_state = filters.ChoiceFilter(
        field_name="proposallearningunit__state",
        label=_('Proposal status'),
        choices=_get_sorted_choices(ProposalState.choices()),
        required=False,
        empty_label=pgettext_lazy("plural", "All"),
    )
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.PROPOSAL_SEARCH.value
    )

    order_by_field = 'ordering'
    ordering = ProposalLearningUnitOrderingFilter(
        fields=(
            ('academic_year__year', 'academic_year'),
            ('acronym', 'acronym'),
            ('full_title', 'title'),
            ('learning_container_year__container_type', 'type'),
            ('entity_requirement', 'requirement_entity'),
            ('proposallearningunit__type', 'proposal_type'),
            ('proposallearningunit__state', 'proposal_state'),
            ('proposallearningunit__folder_id', 'folder'),  # Overrided by ProposalLearningUnitOrderingFilter
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = LearningUnitYear
        fields = [
            "academic_year",
            "acronym",
            "subtype",
            "requirement_entity",
        ]

    def __init__(self, *args, person=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person
        self.queryset = self.get_queryset
        self._get_entity_folder_id_linked_ordered_by_acronym(self.person)

        # Academic year default value = n+1 for proposals search -> use event having n+1 as first open academic year
        event_perm = event_perms.EventPermCreationOrEndDateProposalFacultyManager()
        self.form.fields["academic_year"].initial = event_perm.get_academic_years().first()

    def _get_entity_folder_id_linked_ordered_by_acronym(self, person):
        most_recent_acronym = EntityVersion.objects.filter(
            entity__id=OuterRef('id'),
        ).order_by(
            "-start_date"
        ).values('acronym')[:1]

        entities = Entity.objects.filter(
            proposallearningunit__isnull=False
        ).annotate(
            entity_acronym=Subquery(most_recent_acronym)
        ).distinct().order_by(
            "entity_acronym"
        )

        self.form.fields['entity_folder'].choices = [(ent.pk, ent.entity_acronym)
                                                     for ent in entities]

    def filter_entity(self, queryset, name, value):
        with_subordinated = self.form.cleaned_data['with_entity_subordinated']
        lookup_expression = "__".join(["learning_container_year", name, "in"])
        if value:
            entity_ids = get_entities_ids(value, with_subordinated)
            queryset = queryset.filter(**{lookup_expression: entity_ids})
        return queryset

    def filter_tutor(self, queryset, name, value):
        for tutor_name in value.split():
            filter_by_first_name = Q(
                learningcomponentyear__attributionchargenew__attribution__tutor__person__first_name__iregex=tutor_name
            )
            filter_by_last_name = Q(
                learningcomponentyear__attributionchargenew__attribution__tutor__person__last_name__iregex=tutor_name
            )
            queryset = queryset.filter(
                filter_by_first_name | filter_by_last_name
            ).distinct()
        return queryset

    @property
    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return LearningUnitYear.objects.none()

        entity_folder = EntityVersion.objects.filter(
            entity=OuterRef('proposallearningunit__entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        has_proposal = ProposalLearningUnit.objects.filter(
            learning_unit_year=OuterRef('pk'),
        )

        queryset = LearningUnitYear.objects_with_container.filter(
            proposallearningunit__isnull=False
        ).select_related(
            'academic_year',
            'learning_container_year__academic_year',
            'language',
            'externallearningunityear',
            'campus',
            'proposallearningunit',
            'campus__organization',
        ).prefetch_related(
            "learningcomponentyear_set",
        ).annotate(
            has_proposal=Exists(has_proposal),
            entity_folder=Subquery(entity_folder),
        )

        queryset = LearningUnitYearQuerySet.annotate_full_title_class_method(queryset)
        queryset = LearningUnitYearQuerySet.annotate_entities_allocation_and_requirement_acronym(queryset)

        return queryset


class ProposalStateModelForm(forms.ModelForm):
    class Meta:
        model = ProposalLearningUnit
        fields = ['state']

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        if kwargs.pop('is_faculty_manager', False):
            self.fields['state'].choices = LimitedProposalState.choices()
