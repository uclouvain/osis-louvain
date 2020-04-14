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
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from backoffice.settings.rest_framework.filters import OrderingFilterWithDefault
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums.education_group_types import MiniTrainingType
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.mini_training import MiniTrainingDetailSerializer, MiniTrainingListSerializer
from program_management.models.education_group_version import EducationGroupVersion


class MiniTrainingFilter(filters.FilterSet):
    from_year = filters.NumberFilter(field_name="offer__academic_year__year", lookup_expr='gte')
    to_year = filters.NumberFilter(field_name="offer__academic_year__year", lookup_expr='lte')
    code = filters.CharFilter(field_name="root_group__partial_acronym", lookup_expr='icontains')
    education_group_type = filters.MultipleChoiceFilter(
        field_name='offer__education_group_type__name',
        choices=MiniTrainingType.choices()
    )
    version_type = filters.CharFilter(method='filter_version_type')

    order_by_field = 'ordering'
    ordering = OrderingFilterWithDefault(
        fields=(
            ('offer__acronym', 'acronym'),
            ('root_group__partial_acronym', 'code'),
            ('offer__academic_year__year', 'academic_year'),
            ('offer__title', 'title'),
        ),
        default_ordering=('-offer__academic_year__year', 'offer__acronym',)
    )

    class Meta:
        model = EducationGroupVersion
        fields = [
            'offer__acronym', 'code', 'offer__education_group_type', 'offer__title', 'offer__title_english',
            'from_year', 'to_year', 'version_type',
            'is_transition', 'version_name'
        ]


class MiniTrainingList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all the mini_trainings with optional filtering.
    """
    name = 'minitraining_list'
    queryset = EducationGroupVersion.objects.filter(
        offer__education_group_type__category=education_group_categories.MINI_TRAINING,
        version_name='',
        is_transition=False
    ).select_related('offer__education_group_type', 'offer__academic_year').prefetch_related(
        'offer__management_entity__entityversion_set'
    ).exclude(
        offer__acronym__icontains='common',
    )
    serializer_class = MiniTrainingListSerializer
    filterset_class = MiniTrainingFilter
    search_fields = (
        'offer__acronym',
        'root_group__partial_acronym',
        'offer__title',
        'offer__title_english',
    )


class MiniTrainingDetail(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the detail of the mini training
    """
    name = 'mini_training_read'
    serializer_class = MiniTrainingDetailSerializer

    def get_object(self):
        partial_acronym = self.kwargs['partial_acronym']
        year = self.kwargs['year']
        egv = get_object_or_404(
            EducationGroupVersion.objects.filter(
                offer__education_group_type__category=education_group_categories.MINI_TRAINING,
                version_name='',
                is_transition=False
            ).select_related(
                'offer__education_group_type',
                'offer__academic_year',
                'offer__main_teaching_campus',
            ).prefetch_related(
                'offer__management_entity__entityversion_set',
            ),
            root_group__partial_acronym__iexact=partial_acronym,  # Field moved into GroupYear
            offer__academic_year__year=year
        )
        return egv.offer


class MiniTrainingTitle(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the title of the mini training
    """
    name = 'minitrainingstitle_read'
    serializer_class = EducationGroupTitleSerializer

    def get_object(self):
        acronym = self.kwargs['partial_acronym']
        year = self.kwargs['year']
        egy = get_object_or_404(
            EducationGroupYear.objects.all().select_related('academic_year'),
            partial_acronym__iexact=acronym,
            academic_year__year=year
        )
        return egy
