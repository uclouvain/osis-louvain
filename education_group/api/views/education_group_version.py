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
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.education_group_year import EducationGroupYear
from education_group.api.serializers.education_group_version import TrainingVersionListSerializer, \
    MiniTrainingVersionListSerializer
from program_management.models.education_group_version import EducationGroupVersion


class VersionFilter(filters.FilterSet):
    class Meta:
        model = EducationGroupVersion
        fields = ['is_transition']


class TrainingVersionList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all version of the training.
    """
    name = 'training_versions_list'
    serializer_class = TrainingVersionListSerializer
    filterset_class = VersionFilter
    search_fields = (
        'version_name',
    )

    def get_queryset(self):
        education_group_year = get_object_or_404(
            EducationGroupYear.objects.all(),
            acronym=self.kwargs['acronym'].upper(),
            academic_year__year=self.kwargs['year']
        )
        return EducationGroupVersion.objects.filter(offer=education_group_year, is_transition=False)


class MiniTrainingVersionList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all version of the mini training.
    """
    name = 'mini_training_versions_list'
    serializer_class = MiniTrainingVersionListSerializer
    filterset_class = VersionFilter
    search_fields = (
        'version_name',
    )

    def get_queryset(self):
        version = get_object_or_404(
            EducationGroupVersion.objects.select_related(
                'root_group', 'root_group__academic_year', 'offer'
            ).prefetch_related('offer__educationgroupversion_set'),
            root_group__partial_acronym=self.kwargs['official_partial_acronym'].upper(),
            root_group__academic_year__year=self.kwargs['year']
        )
        return version.offer.educationgroupversion_set.filter(is_transition=False)
