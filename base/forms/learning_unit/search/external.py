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
from django.db.models import BLANK_CHOICE_DASH, OuterRef, Exists
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import FilterSet, filters, OrderingFilter

from base.forms.utils.filter_field import filter_field_by_regex
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.campus import Campus
from base.models.enums import active_status
from base.models.learning_unit_year import LearningUnitYear, LearningUnitYearQuerySet
from base.models.organization_address import OrganizationAddress
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.learning_units.search.common import SearchTypes
from reference.models.country import Country


class ExternalLearningUnitFilter(FilterSet):
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
    title = filters.CharFilter(
        field_name="full_title",
        method="filter_learning_unit_year_field",
        max_length=40,
        label=_('Title'),
    )
    status = filters.ChoiceFilter(
        choices=active_status.ACTIVE_STATUS_LIST_FOR_FILTER,
        required=False,
        label=_('Status'),
        field_name="status",
        empty_label=pgettext_lazy("plural", "All")
    )
    country = filters.ModelChoiceFilter(
        queryset=Country.objects.filter(organizationaddress__isnull=False).distinct().order_by('name'),
        field_name="campus__organization__organizationaddress__country",
        required=False,
        label=_("Country")
    )
    city = filters.ChoiceFilter(
        choices=BLANK_CHOICE_DASH,
        field_name="campus__organization__organizationaddress__city",
        required=False,
        label=_("City"),
        help_text=_("Please select a country first")
    )
    campus = filters.ChoiceFilter(
        choices=BLANK_CHOICE_DASH,
        required=False,
        label=_("Institution"),
        help_text=_("Please select a country and a city first")
    )
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.EXTERNAL_SEARCH.value
    )

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('academic_year__year', 'academic_year'),
            ('acronym', 'acronym'),
            ('full_title', 'title'),
            ('status', 'status'),
            ('campus__organization__name', 'campus'),
            ('credits', 'credits'),
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = LearningUnitYear
        fields = [
            "academic_year",
            "acronym",
            "title",
            "credits",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        self.form.fields["academic_year"].initial = starting_academic_year()

        if self.data.get('country'):
            self._init_dropdown_list()

    def _init_dropdown_list(self):
        if self.data.get('country'):
            self._init_cities_choices()
        if self.data.get('city'):
            self._init_campus_choices()

    def _init_cities_choices(self):
        cities_choices = OrganizationAddress.objects.filter(
            country=self.data["country"]
        ).distinct(
            'city'
        ).order_by(
            'city'
        ).values_list('city', 'city')

        self.form.fields['city'].choices = cities_choices

    def _init_campus_choices(self):
        campus_choices = Campus.objects.filter(
            organization__organizationaddress__city=self.data['city']
        ).distinct(
            'organization__name'
        ).order_by(
            'organization__name'
        ).values_list(
            'pk',
            'organization__name'
        )
        self.form.fields['campus'].choices = campus_choices

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return LearningUnitYear.objects.none()

        has_proposal = ProposalLearningUnit.objects.filter(
            learning_unit_year=OuterRef('pk'),
        )

        qs = LearningUnitYear.objects_with_container.filter(
            externallearningunityear__co_graduation=True,
            externallearningunityear__mobility=False,
        ).select_related(
            'academic_year',
            'learning_container_year__academic_year',
            'language',
            'externallearningunityear',
            'campus',
            'proposallearningunit',
            'campus__organization',
        ).prefetch_related(
            "learningcomponentyear_set"
        ).annotate(
            has_proposal=Exists(has_proposal)
        ).order_by('academic_year__year', 'acronym')

        qs = LearningUnitYearQuerySet.annotate_full_title_class_method(qs)
        qs = LearningUnitYearQuerySet.annotate_entities_allocation_and_requirement_acronym(qs)
        return qs

    def filter_learning_unit_year_field(self, queryset, name, value):
        return filter_field_by_regex(queryset, name, value)
