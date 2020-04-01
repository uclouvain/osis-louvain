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
from dal import autocomplete
from django import forms
from django.db.models import Case, When, Value, CharField, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import OrderingFilter, filters, FilterSet

from base.business.entity import get_entities_ids
from base.forms.utils.filter_field import filter_field_by_regex
from base.models import entity_version
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums import education_group_types
from base.models.enums.education_group_categories import Categories


class EducationGroupFilter(FilterSet):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=False,
        label=_('Ac yr.'),
        empty_label=pgettext_lazy("plural", "All"),
    )
    category = filters.ChoiceFilter(
        choices=list(Categories.choices()),
        required=False,
        label=_('Category'),
        field_name='education_group_type__category',
        empty_label=pgettext_lazy("plural", "All")
    )
    education_group_type = filters.ModelMultipleChoiceFilter(
        queryset=EducationGroupType.objects.none(),
        required=False,
        label=_('Type'),
        widget=autocomplete.ModelSelect2Multiple(
            url='education_group_type_autocomplete',
            forward=['category'],
        ),
    )
    management_entity = filters.CharFilter(
        method='filter_with_entity_subordinated',
        label=_('Entity')
    )
    with_entity_subordinated = filters.BooleanFilter(
        method=lambda queryset, *args, **kwargs: queryset,
        label=_('Include subordinate entities'),
        widget=forms.CheckboxInput
    )
    acronym = filters.CharFilter(
        field_name="acronym",
        method="filter_education_group_year_field",
        max_length=40,
        required=False,
        label=_('Acronym/Short title'),
    )
    title = filters.CharFilter(
        field_name="title",
        method='filter_education_group_year_field',
        max_length=255,
        required=False,
        label=_('Title')
    )
    partial_acronym = filters.CharFilter(
        field_name="partial_acronym",
        method='filter_education_group_year_field',
        max_length=15,
        required=False,
        label=_('Code'),
    )

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('acronym', 'acronym'),
            ('partial_acronym', 'code'),
            ('academic_year__year', 'academic_year'),
            ('title', 'title'),
            ('type_ordering', 'type'),
            ('entity_management_version', 'management_entity')
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = EducationGroupYear
        fields = [
            'acronym',
            'partial_acronym',
            'title',
            'education_group_type__name',
            'management_entity',
            'with_entity_subordinated',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        self.form.fields['education_group_type'].queryset = EducationGroupType.objects.all().order_by_translated_name()
        self.form.fields['academic_year'].initial = starting_academic_year()
        self.form.fields['category'].initial = education_group_categories.TRAINING
        self.form.fields["with_entity_subordinated"].initial = kwargs.pop('with_entity_subordinated', True)

    def filter_with_entity_subordinated(self, queryset, name, value):
        with_subordinated = self.form.cleaned_data['with_entity_subordinated']
        if value:
            entity_ids = get_entities_ids(value, with_subordinated)
            queryset = queryset.filter(management_entity__in=entity_ids)
        return queryset

    @staticmethod
    def filter_education_group_year_field(queryset, name, value):
        return filter_field_by_regex(queryset, name, value)

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return EducationGroupYear.objects.none()

        management_entity = entity_version.EntityVersion.objects.filter(
            entity=OuterRef('management_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        return EducationGroupYear.objects.all().annotate(
            type_ordering=Case(
                *[When(education_group_type__name=key, then=Value(str(_(val))))
                  for i, (key, val) in enumerate(education_group_types.ALL_TYPES)],
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            entity_management_version=Subquery(management_entity)
        )

    def filter_queryset(self, queryset):
        # Order by id to always ensure same order when objects have same values for order field (ex: title)
        qs = super().filter_queryset(queryset)
        order_fields = qs.query.order_by + ('id', )
        return qs.order_by(*order_fields)
