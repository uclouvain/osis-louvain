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
from rest_framework import generics

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from education_group.api.serializers.training import TrainingListSerializer, TrainingDetailSerializer


class TrainingList(generics.ListAPIView):
    """
       Return a list of all the training with optional filtering.
    """
    name = 'training-list'
    queryset = EducationGroupYear.objects.filter(education_group_type__category=education_group_categories.TRAINING)\
                                         .select_related('education_group_type', 'academic_year')\
                                         .prefetch_related(
                                                'administration_entity__entityversion_set',
                                                'management_entity__entityversion_set'
                                         )
    serializer_class = TrainingListSerializer
    filter_fields = (
        'acronym',
        'partial_acronym',
        'title',
        'title_english',
    )
    search_fields = (
        'acronym',
        'partial_acronym',
        'title',
        'title_english',
    )
    ordering_fields = (
        'acronym',
        'partial_acronym',
        'title',
        'title_english',
    )
    ordering = (
        '-academic_year__year',
        'acronym',
    )  # Default ordering


class TrainingDetail(generics.RetrieveAPIView):
    """
        Return the detail of the training
    """
    name = 'training-detail'
    queryset = EducationGroupYear.objects.filter(education_group_type__category=education_group_categories.TRAINING)\
                                         .select_related(
                                            'education_group_type',
                                            'academic_year',
                                            'main_teaching_campus',
                                            'enrollment_campus',
                                            'primary_language',
                                         ).prefetch_related(
                                            'administration_entity__entityversion_set',
                                            'management_entity__entityversion_set',
                                         )
    serializer_class = TrainingDetailSerializer
    lookup_field = 'uuid'
    pagination_class = None
    filter_backends = ()
