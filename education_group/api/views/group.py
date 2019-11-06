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
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.group import GroupDetailSerializer


class GroupDetail(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the detail of the group
    """
    name = 'group_read'
    serializer_class = GroupDetailSerializer

    def get_object(self):
        partial_acronym = self.kwargs['partial_acronym']
        year = self.kwargs['year']
        egy = get_object_or_404(
            EducationGroupYear.objects.filter(
                education_group_type__category=education_group_categories.GROUP
            ).select_related(
                'education_group_type',
                'academic_year',
                'main_teaching_campus',
            ).prefetch_related(
                'management_entity__entityversion_set',
            ),
            partial_acronym__iexact=partial_acronym,
            academic_year__year=year
        )
        return egy


class GroupTitle(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the title of the group
    """
    name = 'groupstitle_read'
    serializer_class = EducationGroupTitleSerializer

    def get_object(self):
        acronym = self.kwargs['partial_acronym']
        year = self.kwargs['year']
        egy = get_object_or_404(
            EducationGroupYear.objects.all().select_related(
                'academic_year',
            ),
            partial_acronym__iexact=acronym,
            academic_year__year=year
        )
        return egy
