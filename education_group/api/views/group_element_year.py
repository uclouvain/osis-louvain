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
from rest_framework.generics import get_object_or_404

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from education_group.api.serializers.group_element_year import EducationGroupRootNodeTreeSerializer
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.ddd.domain import link
from program_management.ddd.repositories import load_tree


class EducationGroupTreeView(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    serializer_class = EducationGroupRootNodeTreeSerializer
    filter_backends = []
    paginator = None
    lookup_fields = ('academic_year__year', 'acronym__iexact',)
    lookup_url_kwargs = ('year', 'acronym',)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        filter_kwargs = {
            lookup_field: self.kwargs[lookup_url_kwarg]
            for lookup_field, lookup_url_kwarg in zip(self.lookup_fields, self.lookup_url_kwargs)
        }
        education_group_year = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, education_group_year)

        tree = load_tree.load(education_group_year.id)
        return link.factory.get_link(parent=None, child=tree.root_node)


class TrainingTreeView(EducationGroupTreeView):
    """
        Return the tree of the training
    """
    name = 'trainings_tree'
    queryset = EducationGroupYear.objects.filter(
        education_group_type__category=Categories.TRAINING.name
    )


class MiniTrainingTreeView(EducationGroupTreeView):
    """
        Return the tree of the mini-training
    """
    name = 'minitrainings_tree'
    lookup_fields = ('academic_year__year', 'partial_acronym__iexact',)
    lookup_url_kwargs = ('year', 'partial_acronym',)
    queryset = EducationGroupYear.objects.filter(
        education_group_type__category=Categories.MINI_TRAINING.name
    )


class GroupTreeView(EducationGroupTreeView):
    """
        Return the tree of the group
    """
    name = 'groups_tree'
    lookup_fields = ('academic_year__year', 'partial_acronym__iexact',)
    lookup_url_kwargs = ('year', 'partial_acronym',)
    queryset = EducationGroupYear.objects.filter(
        education_group_type__category=Categories.GROUP.name
    )
