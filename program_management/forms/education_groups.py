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
from django.db.models import Q
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import OrderingFilter, filters, FilterSet

from base.business.entity import get_entities_ids
from base.forms.utils.filter_field import filter_field_by_regex
from base.models import entity_version
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories
from base.models.enums import education_group_types
from base.models.enums.education_group_categories import Categories
from education_group.models.group_year import GroupYear

PARTICULAR = "PARTICULAR"
STANDARD = "STANDARD"

VERSION_CHOICES = (
    (STANDARD, _("Standard")),
    (PARTICULAR, _("Particulière")),
)


class GroupFilter(FilterSet):
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
    title_fr = filters.CharFilter(
        field_name="title_fr",
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

    version = filters.ChoiceFilter(
        choices=list(VERSION_CHOICES),
        required=False,
        label=_('Version'),
        field_name='version',
        empty_label=pgettext_lazy("plural", "All"),
    )

    with_entity_transition = filters.BooleanFilter(
        method="filter_by_transition",
        label=_('Include transition'),
        widget=forms.CheckboxInput,
        initial='True'
    )

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('acronym', 'acronym'),
            ('partial_acronym', 'code'),
            ('academic_year__year', 'academic_year'),
            ('title_fr', 'title_fr'),
            ('type_ordering', 'type'),
            ('entity_management_version', 'management_entity')
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = GroupYear
        fields = [
            'acronym',
            'partial_acronym',
            'title_fr',
            'education_group_type__name',
            'management_entity',
            'with_entity_subordinated',
            'version',
            'with_entity_transition'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        self.form.fields['education_group_type'].queryset = EducationGroupType.objects.all().order_by_translated_name()
        self.form.fields['academic_year'].initial = starting_academic_year()
        self.form.fields['category'].initial = education_group_categories.TRAINING
        self.form.fields["with_entity_subordinated"].initial = kwargs.pop('with_entity_subordinated', True)
        self.form.fields["version"].initial = kwargs.pop('version', None)

    def filter_with_entity_subordinated(self, queryset, name, value):
        with_subordinated = self.form.cleaned_data['with_entity_subordinated']
        if value:
            entity_ids = get_entities_ids(value, with_subordinated)
            queryset = queryset.filter(management_entity__in=entity_ids)
        return queryset

    @staticmethod
    def filter_education_group_year_field(queryset, name, value):
        return filter_field_by_regex(queryset, name, value)

    def filter_by_transition(self, queryset, name, value):
        if not value:
            return queryset.exclude(educationgroupversion__is_transition=True)
        return queryset

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return GroupYear.objects.none()

        management_entity = entity_version.EntityVersion.objects.filter(
            entity=OuterRef('management_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        return GroupYear.objects.all().annotate(
            type_ordering=Case(
                *[When(education_group_type__name=key, then=Value(str(_(val))))
                  for i, (key, val) in enumerate(education_group_types.ALL_TYPES)],
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            entity_management_version=Subquery(management_entity)
        ).annotate(
            version=Case(
                When(~Q(Q(educationgroupversion__version_name='') | Q(educationgroupversion__isnull=True)),
                     then=Value(PARTICULAR)),
                default=Value(STANDARD),
                output_field=CharField(),)
        ).annotate(
            complete_title_fr=Case(
                When(
                    Q(educationgroupversion__isnull=False),
                    then=Case(
                        When(Q(educationgroupversion__is_transition=True) &
                             Q(educationgroupversion__version_name=''),
                             then=Concat('acronym', Value('[Transition]'))),
                        When(~Q(educationgroupversion__version_name='') &
                             Q(educationgroupversion__is_transition=True),
                             then=Concat('acronym',  Value('['), 'educationgroupversion__version_name', Value('-Transition]'))),
                        When(~Q(educationgroupversion__version_name='') &
                             Q(educationgroupversion__is_transition=False),
                             then=Concat('acronym',  Value('['), 'educationgroupversion__version_name', Value(']'))),
                        default='acronym',
                        output_field=CharField()
                    )
                ),
                default='acronym',
                output_field=CharField()
            )
        ).annotate(
            title=Case(
                When(Q(educationgroupversion__isnull=False) & ~Q(educationgroupversion__title_fr=''),
                     then=Concat('title_fr', Value(' ['), 'educationgroupversion__title_fr', Value(']'))),
                default='title_fr',
                output_field=CharField(),)
        )

    def filter_queryset(self, queryset):
        # Order by id to always ensure same order when objects have same values for order field (ex: title)
        qs = super().filter_queryset(queryset)
        order_fields = qs.query.order_by + ('id', )
        return qs.order_by(*order_fields)

