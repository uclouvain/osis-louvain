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

from django.conf import settings
from rest_framework import serializers

from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories
from education_group.api.serializers import utils
from education_group.api.serializers.utils import GroupHyperlinkedIdentityField
from education_group.models.group_year import GroupYear


class GroupTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = GroupYear
        fields = (
            'title',
        )

    def get_title(self, education_group_year):
        language = self.context.get('language')
        return getattr(
            education_group_year,
            'title_' + ('en' if language and language not in settings.LANGUAGE_CODE_FR else 'fr')
        )


class GroupDetailSerializer(GroupTitleSerializer, serializers.ModelSerializer):
    url = GroupHyperlinkedIdentityField(read_only=True)
    code = serializers.CharField(source='partial_acronym', read_only=True)
    academic_year = serializers.SlugRelatedField(slug_field='year', queryset=AcademicYear.objects.all())
    education_group_type = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EducationGroupType.objects.filter(category=education_group_categories.GROUP),
    )
    management_entity = serializers.CharField(source='management_entity_version.acronym', read_only=True)
    management_faculty = serializers.SerializerMethodField()
    remark = serializers.SerializerMethodField()
    # TODO: Field to add into model
    # campus = CampusDetailSerializer(source='main_teaching_campus', read_only=True)

    # Display human readable value
    education_group_type_text = serializers.CharField(source='education_group_type.get_name_display', read_only=True)
    constraint_type_text = serializers.CharField(source='get_constraint_type_display', read_only=True)

    class Meta(GroupTitleSerializer.Meta):
        fields = GroupTitleSerializer.Meta.fields + (
            'url',
            'acronym',
            'code',
            'management_entity',
            'management_faculty',
            'academic_year',
            'education_group_type',
            'education_group_type_text',
            'credits',
            'min_constraint',
            'max_constraint',
            'constraint_type',
            'constraint_type_text',
            'remark',
            # 'campus',
        )

    def get_remark(self, education_group_year):
        language = self.context.get('language')
        return getattr(
            education_group_year,
            'remark_' + ('en' if language and language not in settings.LANGUAGE_CODE_FR else 'fr')
        )

    @staticmethod
    def get_management_faculty(obj):
        return utils.get_entity(obj, 'management')
