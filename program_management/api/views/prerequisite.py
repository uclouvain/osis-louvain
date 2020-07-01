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
from base.models.enums import education_group_categories
from program_management.api.serializers.prerequisite import ProgramTreePrerequisitesSerializer
from program_management.ddd.repositories import load_tree
from program_management.models.education_group_version import EducationGroupVersion


class ProgramTreePrerequisites(LanguageContextSerializerMixin, generics.ListAPIView):
    """
        Return the prerequisites of a program tree
    """
    NAME = 'program_tree-prerequisites'
    serializer_class = ProgramTreePrerequisitesSerializer
    queryset = EducationGroupVersion.objects.all().select_related('offer__academic_year')
    pagination_class = None
    filter_backends = ()
    tree = None

    def get_tree(self):
        return self.tree

    def get_queryset(self):
        self.get_serializer_context()
        return self.get_tree().get_nodes_that_have_prerequisites() if self.get_tree() else None

    def get_object(self):
        acronym = self.kwargs['acronym']
        year = self.kwargs['year']
        version_name = self.kwargs.get('version_name', '')
        is_transition = self.kwargs['transition']
        return get_object_or_404(
            self.queryset,
            version_name__iexact=version_name,
            is_transition=is_transition,
            offer__acronym__iexact=acronym,
            offer__academic_year__year=year
        )

    def get_serializer_context(self):
        education_group_version = self.get_object()
        self.tree = load_tree.load(education_group_version.offer.id)
        serializer_context = super().get_serializer_context()
        serializer_context.update({
            'request': self.request,
            'tree': self.get_tree()
        })
        return serializer_context


class TrainingPrerequisites(ProgramTreePrerequisites):
    NAME = 'training-prerequisites'
    queryset = EducationGroupVersion.objects.filter(
        offer__education_group_type__category=education_group_categories.TRAINING
    ).select_related('offer__education_group_type', 'offer__academic_year')


class MiniTrainingPrerequisites(ProgramTreePrerequisites):
    NAME = 'mini_training-prerequisites'
    queryset = EducationGroupVersion.objects.filter(
        offer__education_group_type__category=education_group_categories.MINI_TRAINING
    ).select_related('offer__education_group_type', 'offer__academic_year')

    def get_object(self):
        partial_acronym = self.kwargs['partial_acronym']
        year = self.kwargs['year']
        version_name = self.kwargs.get('version_name', '')
        is_transition = self.kwargs['transition']
        return get_object_or_404(
            self.queryset,
            version_name=version_name,
            is_transition=is_transition,
            offer__partial_acronym__iexact=partial_acronym,
            offer__academic_year__year=year
        )
