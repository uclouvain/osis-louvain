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
from rest_framework import serializers

from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.prerequisite import Prerequisite
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.utils import StandardVersionHyperlinkedRelatedField, \
    FlattenMixin, StandardVersionHyperlinkedIdentityField


class BaseLearningUnitOfferSerializer(EducationGroupTitleSerializer, serializers.HyperlinkedModelSerializer):
    academic_year = serializers.IntegerField(source='academic_year.year')
    education_group_type = serializers.SlugRelatedField(slug_field='name', queryset=EducationGroupType.objects.all())
    code = serializers.CharField(source='partial_acronym', read_only=True)
    education_group_type_text = serializers.CharField(source='education_group_type.get_name_display', read_only=True)

    class Meta:
        model = EducationGroupYear
        fields = EducationGroupTitleSerializer.Meta.fields + (
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
        )


class EducationGroupRootsListSerializer(BaseLearningUnitOfferSerializer, serializers.HyperlinkedModelSerializer):
    url = StandardVersionHyperlinkedIdentityField(read_only=True)

    # Display human readable value
    decree_category_text = serializers.CharField(source='get_decree_category_display', read_only=True)
    duration_unit_text = serializers.CharField(source='get_duration_unit_display', read_only=True)

    class Meta:
        model = EducationGroupYear
        fields = (
            'url',
            'credits',
            'decree_category',
            'decree_category_text',
            'duration',
            'duration_unit',
            'duration_unit_text',
        ) + BaseLearningUnitOfferSerializer.Meta.fields


class LearningUnitYearPrerequisitesListSerializer(FlattenMixin, serializers.ModelSerializer):
    url = StandardVersionHyperlinkedRelatedField(source='education_group_year', lookup_field='acronym', read_only=True)
    prerequisites = serializers.CharField(source='prerequisite_string')

    class Meta:
        flatten = [('education_group_year', BaseLearningUnitOfferSerializer)]
        model = Prerequisite
        fields = (
            'url',
            'prerequisites'
        )
