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
from django.conf import settings
from rest_framework import serializers

from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.prerequisite import Prerequisite
from education_group.api.serializers.training import TrainingHyperlinkedIdentityField
from education_group.api.serializers.utils import TrainingHyperlinkedRelatedField


class EducationGroupRootsTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupYear
        fields = (
            'title',
        )

    def get_title(self, education_group_year):
        language = self.context['language']
        return getattr(
            education_group_year,
            'title' + ('_english' if language not in settings.LANGUAGE_CODE_FR else '')
        )


class EducationGroupRootsListSerializer(EducationGroupRootsTitleSerializer, serializers.HyperlinkedModelSerializer):
    url = TrainingHyperlinkedIdentityField(read_only=True)
    academic_year = serializers.IntegerField(source='academic_year.year')
    education_group_type = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EducationGroupType.objects.all(),
    )
    code = serializers.CharField(source='partial_acronym', read_only=True)

    # Display human readable value
    education_group_type_text = serializers.CharField(source='education_group_type.get_name_display', read_only=True)
    decree_category_text = serializers.CharField(source='get_decree_category_display', read_only=True)
    duration_unit_text = serializers.CharField(source='get_duration_unit_display', read_only=True)

    class Meta:
        model = EducationGroupYear
        fields = EducationGroupRootsTitleSerializer.Meta.fields + (
            'url',
            'acronym',
            'code',
            'credits',
            'decree_category',
            'decree_category_text',
            'duration',
            'duration_unit',
            'duration_unit_text',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
        )


class LearningUnitYearPrerequisitesListSerializer(serializers.ModelSerializer):
    url = TrainingHyperlinkedRelatedField(source='education_group_year', lookup_field='acronym', read_only=True)

    acronym = serializers.CharField(source='education_group_year.acronym')
    code = serializers.CharField(source='education_group_year.partial_acronym')
    academic_year = serializers.IntegerField(source='education_group_year.academic_year.year')
    education_group_type = serializers.SlugRelatedField(
        source='education_group_year.education_group_type',
        slug_field='name',
        queryset=EducationGroupType.objects.all(),
    )
    education_group_type_text = serializers.CharField(
        source='education_group_year.education_group_type.get_name_display',
        read_only=True,
    )
    prerequisites = serializers.CharField(source='prerequisite_string')
    title = serializers.SerializerMethodField()

    class Meta:
        model = Prerequisite
        fields = (
            'url',
            'title',
            'acronym',
            'code',
            'academic_year',
            'education_group_type',
            'education_group_type_text',
            'prerequisites'
        )

    def get_title(self, prerequisite):
        language = self.context['language']
        return getattr(
            prerequisite.education_group_year,
            'title' + ('_english' if language not in settings.LANGUAGE_CODE_FR else '')
        )
