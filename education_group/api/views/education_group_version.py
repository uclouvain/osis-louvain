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
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.education_group_year import EducationGroupYear
from education_group.api.serializers.education_group_version import VersionListSerializer
from education_group.models.group_year import GroupYear
from program_management.models.education_group_version import EducationGroupVersion


class TrainingVersionList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all version of the training.
    """
    name = 'training_versions_list'
    serializer_class = VersionListSerializer
    search_fields = (
        'is_transition',
        'version_name',
    )

    def get_queryset(self):
        education_group_year = get_object_or_404(
            EducationGroupYear.objects.all(),
            acronym=self.kwargs['acronym'].upper(),
            academic_year__year=self.kwargs['year']
        )
        return EducationGroupVersion.objects.filter(offer=education_group_year)


class MiniTrainingVersionList(LanguageContextSerializerMixin, generics.ListAPIView):
    """
       Return a list of all version of the mini training.
    """
    name = 'minitraining_versions_list'
    serializer_class = VersionListSerializer
    search_fields = (
        'is_transition',
        'version_name',
    )

    def get_queryset(self):
        group_year = get_object_or_404(
            GroupYear.objects.all().select_related('educationgroupversion__offer'),
            partial_acronym=self.kwargs['partial_acronym'].upper(),
            academic_year__year=self.kwargs['year'],
            educationgroupversion__version_name='',
            educationgroupversion__is_transition=False
        )
        return EducationGroupVersion.objects.filter(offer=group_year.educationgroupversion.offer)
