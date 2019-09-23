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

from base.models.learning_unit_year import LearningUnitYear
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer, LearningUnitSerializer


class LearningUnitFilter(filters.FilterSet):
    acronym_like = filters.CharFilter(field_name="acronym", lookup_expr='icontains')
    year = filters.NumberFilter(field_name="academic_year__year")

    class Meta:
        model = LearningUnitYear
        fields = ['acronym', 'acronym_like', 'year']


class LearningUnitList(generics.ListAPIView):
    """
       Return a list of all the learning unit with optional filtering.
    """
    name = 'learningunits_list'
    queryset = LearningUnitYear.objects.all().select_related(
        'academic_year',
        'learning_container_year'
    ).prefetch_related(
        'learning_container_year__requirement_entity__entityversion_set',
    ).annotate_full_title()
    serializer_class = LearningUnitSerializer
    filter_class = LearningUnitFilter
    search_fields = None
    ordering_fields = None
    ordering = (
        '-academic_year__year',
        'acronym',
    )  # Default ordering


class LearningUnitDetailed(generics.RetrieveAPIView):
    """
        Return the detail of the learning unit
    """
    name = 'learningunits_read'
    queryset = LearningUnitYear.objects.all().select_related(
        'language',
        'campus',
        'academic_year',
        'learning_container_year'
    ).prefetch_related(
        'learning_container_year__requirement_entity__entityversion_set',
        'learningcomponentyear_set'
    ).annotate_full_title()
    serializer_class = LearningUnitDetailedSerializer
    lookup_field = 'uuid'
