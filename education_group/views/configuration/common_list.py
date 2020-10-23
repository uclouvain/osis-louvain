##############################################################################
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
##############################################################################
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import pgettext_lazy, gettext_lazy as _
from django_filters import FilterSet, filters, OrderingFilter
from django_filters.views import FilterView
from rest_framework import serializers

from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin
from osis_role.contrib.views import PermissionRequiredMixin


class CommonListFilter(FilterSet):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=False,
        label=_('Ac yr.'),
        empty_label=pgettext_lazy("female plural", "All"),
    )
    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('acronym', 'acronym'),
            ('academic_year__year', 'academic_year'),
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = EducationGroupYear
        fields = [
            'academic_year'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        self.form.fields['academic_year'].initial = starting_academic_year()

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        if not self.data:
            return EducationGroupYear.objects.none()

        return EducationGroupYear.objects.look_for_common().select_related('academic_year', 'education_group_type')


class CommonListFilterSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()
    acronym = serializers.CharField()
    academic_year = serializers.StringRelatedField()

    class Meta:
        fields = (
            'url',
            'acronym',
            'academic_year',
        )

    def get_url(self, education_group_year) -> str:
        if education_group_year.is_main_common:
            return reverse('common_general_information', kwargs={'year': education_group_year.academic_year.year})
        elif education_group_year.education_group_type.name == TrainingType.BACHELOR.name:
            return reverse(
                'common_bachelor_admission_condition',
                kwargs={'year': education_group_year.academic_year.year}
            )
        elif education_group_year.education_group_type.name == TrainingType.AGGREGATION.name:
            return reverse(
                'common_aggregate_admission_condition',
                kwargs={'year': education_group_year.academic_year.year}
            )
        elif education_group_year.education_group_type.name == TrainingType.PGRM_MASTER_120.name:
            return reverse(
                'common_master_admission_condition',
                kwargs={'year': education_group_year.academic_year.year}
            )
        elif education_group_year.education_group_type.name == TrainingType.MASTER_MC.name:
            return reverse(
                'common_master_specialized_admission_condition',
                kwargs={'year': education_group_year.academic_year.year}
            )
        return "#"


class CommonListView(PermissionRequiredMixin, CacheFilterMixin, SearchMixin, FilterView):
    # PermissionRequiredMixin
    permission_required = 'base.can_access_catalog_configuration'
    raise_exception = True
    template_name = "education_group_app/configuration/common_list.html"

    model = EducationGroupYear
    filterset_class = CommonListFilter

    serializer_class = CommonListFilterSerializer
    cache_search = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["paginator"].count == 0 and self.request.GET:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return {
            **context,
            'form': context["filter"].form,
            'object_list_count': context["paginator"].count,
            'items_per_page': context["paginator"].per_page,
        }
