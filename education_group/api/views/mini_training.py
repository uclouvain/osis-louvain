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

import program_management.ddd.repositories.find_roots
from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from backoffice.settings.rest_framework.filters import OrderingFilterWithDefault
from base.models.enums import education_group_categories
from base.models.enums.education_group_types import MiniTrainingType
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.mini_training import MiniTrainingDetailSerializer, MiniTrainingListSerializer
from education_group.api.serializers.training import TrainingListSerializer
from education_group.api.views import utils
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element


class MiniTrainingFilter(filters.FilterSet):
    from_year = filters.NumberFilter(field_name="offer__academic_year__year", lookup_expr='gte')
    to_year = filters.NumberFilter(field_name="offer__academic_year__year", lookup_expr='lte')
    code = filters.CharFilter(field_name="root_group__partial_acronym", lookup_expr='icontains')
    partial_acronym = filters.CharFilter(field_name="root_group__partial_acronym", lookup_expr='icontains')
    education_group_type = filters.MultipleChoiceFilter(
        field_name='offer__education_group_type__name',
        choices=MiniTrainingType.choices()
    )
    campus = filters.CharFilter(field_name='root_group__main_teaching_campus__name', lookup_expr='icontains')
    version_type = filters.CharFilter(method='filter_version_type')
    acronym = filters.CharFilter(field_name="offer__acronym", lookup_expr='icontains')
    title = filters.CharFilter(field_name="root_group__title_fr", lookup_expr='icontains')
    title_english = filters.CharFilter(field_name="root_group__title_en", lookup_expr='icontains')
    year = filters.NumberFilter(field_name="offer__academic_year__year")

    order_by_field = 'ordering'
    ordering = OrderingFilterWithDefault(
        fields=(
            ('offer__acronym', 'acronym'),
            ('root_group__partial_acronym', 'code'),
            ('offer__academic_year__year', 'academic_year'),
            ('root_group__title_fr', 'title'),
        ),
        default_ordering=('-offer__academic_year__year', 'offer__acronym',)
    )

    class Meta:
        model = EducationGroupVersion
        fields = [
            'acronym', 'code', 'education_group_type', 'title', 'title_english',
            'from_year', 'to_year', 'version_type',
            'is_transition', 'version_name'
        ]

    @staticmethod
    def filter_version_type(queryset, _, value):
        qs = EducationGroupVersion.objects.filter(
            offer__education_group_type__category=education_group_categories.MINI_TRAINING,
        ).select_related(
            'offer__education_group_type',
            'offer__academic_year',
            'root_group'
        ).prefetch_related(
            'offer__management_entity__entityversion_set'
        ).exclude(
            offer__acronym__icontains='common',
        )
        return utils.filter_version_type(qs, value)


class MiniTrainingList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all the mini_trainings with optional filtering.
    """
    name = 'minitraining_list'
    queryset = EducationGroupVersion.objects.filter(
        offer__education_group_type__category=education_group_categories.MINI_TRAINING,
        is_transition=False
    ).select_related(
        'offer__education_group_type',
        'offer__academic_year',
        'root_group'
    ).prefetch_related(
        'offer__management_entity__entityversion_set'
    ).exclude(
        offer__acronym__icontains='common',
    )
    serializer_class = MiniTrainingListSerializer
    filterset_class = MiniTrainingFilter
    search_fields = (
        'offer__acronym',
        'root_group__partial_acronym',
        'root_group__title_fr',
        'root_group__title_en',
    )


class MiniTrainingDetail(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the detail of the mini training
    """
    name = 'mini_training_read'
    serializer_class = MiniTrainingDetailSerializer

    def get_object(self):
        acronym = self.kwargs['acronym']
        year = self.kwargs['year']
        version_name = self.kwargs.get('version_name', '')

        egv = get_object_or_404(
            EducationGroupVersion.objects.filter(
                offer__education_group_type__category=education_group_categories.MINI_TRAINING,
            ).select_related(
                'offer__education_group_type',
                'offer__academic_year',
                'root_group__main_teaching_campus',
                'root_group'
            ).prefetch_related(
                'offer__management_entity__entityversion_set',
            ),
            offer__acronym__iexact=acronym,
            offer__academic_year__year=year,
            version_name__iexact=version_name,
            is_transition=False
        )
        return egv


class MiniTrainingTitle(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the title of the mini training
    """
    name = 'minitrainingstitle_read'
    serializer_class = EducationGroupTitleSerializer

    def get_object(self):
        acronym = self.kwargs['acronym']
        year = self.kwargs['year']
        version_name = self.kwargs.get('version_name', '')

        egv = get_object_or_404(
            EducationGroupVersion.objects.filter(
                offer__education_group_type__category=education_group_categories.MINI_TRAINING,
            ).select_related(
                'offer__academic_year',
                'root_group'
            ),
            offer__acronym__iexact=acronym,
            root_group__academic_year__year=year,
            version_name__iexact=version_name,
            is_transition=False
        )
        return egv


class OfferRoots(LanguageContextSerializerMixin, generics.ListAPIView):
    """
        Return the list of offer roots for a mini training.
    """
    name = 'offer_roots'
    serializer_class = TrainingListSerializer

    def get_queryset(self):
        acronym = self.kwargs['acronym']
        year = self.kwargs['year']
        version_name = self.kwargs.get('version_name', '')

        element = get_object_or_404(
            Element.objects.all().select_related(
                'group_year__academic_year',
            ),
            group_year__educationgroupversion__offer__acronym__iexact=acronym,
            group_year__academic_year__year=year,
            group_year__educationgroupversion__version_name__iexact=version_name
        )
        root_elements = program_management.ddd.repositories.find_roots.find_roots(
            [element],
            as_instances=True
        ).get(element.id, [])
        return EducationGroupVersion.objects.filter(
            root_group__element__in=root_elements
        ).select_related('root_group__academic_year', 'root_group__education_group_type')
