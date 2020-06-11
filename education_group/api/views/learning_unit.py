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
import program_management.ddd.repositories.find_roots
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.enums.education_group_types import GroupType, TrainingType
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from education_group.api.serializers.learning_unit import EducationGroupRootsListSerializer, \
    LearningUnitYearPrerequisitesListSerializer
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element


class EducationGroupRootsFilter(filters.FilterSet):
    ignore_complementary_module = filters.BooleanFilter(method='filter_complementary_module')

    @staticmethod
    def filter_complementary_module(queryset, _, value):
        if value:
            queryset = queryset.exclude(offer__education_group_type__name=GroupType.COMPLEMENTARY_MODULE.name)
        return queryset


class EducationGroupRootsList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return all education groups root which utilize the learning unit specified
    """
    name = 'learningunitutilization_read'
    serializer_class = EducationGroupRootsListSerializer
    filterset_class = EducationGroupRootsFilter
    paginator = None

    def get_queryset(self):
        element = get_object_or_404(
            Element.objects.all().select_related('learning_unit_year__academic_year'),
            learning_unit_year__acronym=self.kwargs['acronym'].upper(),
            learning_unit_year__academic_year__year=self.kwargs['year']
        )
        root_elements = program_management.ddd.repositories.find_roots.find_roots(
            [element],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE],
            exclude_root_categories=TrainingType.finality_types_enum(),
            as_instances=True
        ).get(element.id, [])

        return EducationGroupVersion.objects.filter(
            root_group__element__in=root_elements
        ).select_related('offer__education_group_type', 'offer__academic_year')


class LearningUnitPrerequisitesList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
        Returns all education groups for which this learning unit year had prerequisites
    """
    name = 'learningunitprerequisites_read'
    serializer_class = LearningUnitYearPrerequisitesListSerializer
    filter_backends = []
    paginator = None

    def get_queryset(self):
        learning_unit_year = get_object_or_404(
            LearningUnitYear.objects.all(),
            acronym=self.kwargs['acronym'].upper(),
            academic_year__year=self.kwargs['year']
        )

        return Prerequisite.objects.filter(learning_unit_year=learning_unit_year).select_related(
            'learning_unit_year__academic_year',
            'education_group_version__offer__academic_year',
            'education_group_version__offer__education_group_type'
        ).prefetch_related(
            'prerequisiteitem_set',
        )
