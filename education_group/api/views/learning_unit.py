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

from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.generics import get_object_or_404

import program_management.ddd.repositories.find_roots
from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models import group_element_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType, TrainingType
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from education_group.api.serializers.learning_unit import EducationGroupRootsListSerializer, \
    LearningUnitYearPrerequisitesListSerializer


class EducationGroupRootsFilter(filters.FilterSet):
    ignore_complementary_module = filters.BooleanFilter(method='filter_complementary_module')

    @staticmethod
    def filter_complementary_module(queryset, _, value):
        if value:
            queryset = queryset.exclude(education_group_type__name=GroupType.COMPLEMENTARY_MODULE.name)
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
        learning_unit_year = get_object_or_404(
            LearningUnitYear.objects.all().select_related('academic_year'),
            acronym=self.kwargs['acronym'].upper(),
            academic_year__year=self.kwargs['year']
        )
        education_group_root_ids = program_management.ddd.repositories.find_roots.find_roots(
            [learning_unit_year],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE],
            exclude_root_categories=TrainingType.finality_types_enum()
        ).get(learning_unit_year.id, [])

        return EducationGroupYear.objects.filter(
            pk__in=education_group_root_ids
        ).select_related('education_group_type', 'academic_year')


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
        return Prerequisite.objects.filter(learning_unit_year=learning_unit_year)\
                                   .select_related(
                                        'education_group_year__academic_year',
                                        'education_group_year__education_group_type',
                                        'learning_unit_year__academic_year',
                                   ).prefetch_related('prerequisiteitem_set')
