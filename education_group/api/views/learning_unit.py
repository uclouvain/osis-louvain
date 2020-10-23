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
from django.db.models.expressions import RawSQL
from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.generics import get_object_or_404

import program_management.ddd.repositories.find_roots
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
        self.element = get_object_or_404(
            Element.objects.all().select_related('learning_unit_year__academic_year'),
            learning_unit_year__acronym=self.kwargs['acronym'].upper(),
            learning_unit_year__academic_year__year=self.kwargs['year']
        )
        root_elements = program_management.ddd.repositories.find_roots.find_roots(
            [self.element],
            additional_root_categories=[GroupType.COMPLEMENTARY_MODULE],
            exclude_root_categories=TrainingType.finality_types_enum(),
            as_instances=True
        ).get(self.element.id, [])

        return EducationGroupVersion.objects.filter(
            root_group__element__in=root_elements
        ).select_related('offer__academic_year', 'offer__education_group_type').annotate(
            relative_credits=RawSQL(
                self.get_extra_query(),
                (self.element.id,)
            )
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'learning_unit_year': self.element.learning_unit_year
        })
        return context

    @staticmethod
    def get_extra_query():
        return """
            WITH RECURSIVE group_element_year_children AS (
                SELECT gey.child_element_id, gey.relative_credits
                FROM base_groupelementyear gey
                JOIN program_management_element parent_element ON parent_element.id = gey.parent_element_id
                JOIN education_group_groupyear parent_groupyear ON parent_groupyear.id = parent_element.group_year_id
                JOIN program_management_educationgroupversion parent_version
                ON parent_version.root_group_id = parent_groupyear.id
                WHERE parent_version.id = (
                    SELECT version.id
                    FROM program_management_educationgroupversion version
                    JOIN education_group_groupyear group_year ON version.root_group_id = group_year.id
                    JOIN program_management_element element ON group_year.id = element.group_year_id
                    WHERE version.id = program_management_educationgroupversion.id
                )
                UNION ALL
                SELECT child.child_element_id, child.relative_credits
                FROM base_groupelementyear AS child
                INNER JOIN group_element_year_children AS parent on parent.child_element_id = child.parent_element_id
            )
            SELECT geyc.relative_credits
            FROM group_element_year_children geyc
            JOIN program_management_element element ON geyc.child_element_id = element.id
            WHERE element.id = %s LIMIT 1
        """


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
