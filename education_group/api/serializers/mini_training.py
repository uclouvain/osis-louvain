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
from django.db.models import Case, Value, BooleanField, When
from rest_framework import serializers

from base.api.serializers.campus import CampusDetailSerializer
from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories
from education_group.api.serializers import utils
from education_group.api.serializers.education_group_title import EducationGroupTitleAllLanguagesSerializer
from education_group.api.serializers.education_group_version import MiniTrainingVersionListSerializer
from education_group.api.serializers.utils import MiniTrainingHyperlinkedIdentityField
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION


class MiniTrainingListSerializer(EducationGroupTitleAllLanguagesSerializer, serializers.ModelSerializer):
    url = MiniTrainingHyperlinkedIdentityField(read_only=True)
    acronym = serializers.CharField(source='offer.acronym')
    code = serializers.CharField(source='root_group.partial_acronym')
    academic_year = serializers.SlugRelatedField(
        source='offer.academic_year',
        slug_field='year',
        queryset=AcademicYear.objects.all()
    )
    education_group_type = serializers.SlugRelatedField(
        source='offer.education_group_type',
        slug_field='name',
        queryset=EducationGroupType.objects.filter(category=education_group_categories.MINI_TRAINING),
    )
    management_entity = serializers.CharField(source='offer.management_entity_version.acronym', read_only=True)
    management_faculty = serializers.SerializerMethodField()

    # Display human readable value
    education_group_type_text = serializers.CharField(
        source='offer.education_group_type.get_name_display',
        read_only=True
    )

    class Meta(EducationGroupTitleAllLanguagesSerializer.Meta):
        fields = EducationGroupTitleAllLanguagesSerializer.Meta.fields + (
            'url',
            'version_name',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
            'management_entity',
            'management_faculty',
        )

    @staticmethod
    def get_management_faculty(obj):
        return utils.get_entity(obj.offer, 'management')


class MiniTrainingDetailSerializer(MiniTrainingListSerializer):
    remark = serializers.CharField(source='root_group.remark_fr', read_only=True)
    remark_en = serializers.CharField(source='root_group.remark_en', read_only=True)
    campus = CampusDetailSerializer(source='root_group.main_teaching_campus', read_only=True)
    active = serializers.CharField(source='offer.active', read_only=True)
    schedule_type = serializers.CharField(source='offer.schedule_type', read_only=True)
    keywords = serializers.CharField(source='offer.keywords', read_only=True)
    credits = serializers.IntegerField(source='root_group.credits', read_only=True)
    min_constraint = serializers.IntegerField(source='root_group.min_constraint', read_only=True)
    max_constraint = serializers.IntegerField(source='root_group.max_constraint', read_only=True)
    constraint_type = serializers.CharField(source='root_group.constraint_type', read_only=True)

    # Display human readable value
    constraint_type_text = serializers.CharField(source='root_group.get_constraint_type_display', read_only=True)
    active_text = serializers.CharField(source='offer.get_active_display', read_only=True)
    schedule_type_text = serializers.CharField(source='offer.get_schedule_type_display', read_only=True)

    versions = serializers.SerializerMethodField()

    class Meta(MiniTrainingListSerializer.Meta):
        fields = MiniTrainingListSerializer.Meta.fields + (
            'active',
            'active_text',
            'schedule_type',
            'schedule_type_text',
            'keywords',
            'credits',
            'min_constraint',
            'max_constraint',
            'constraint_type',
            'constraint_type_text',
            'remark',
            'remark_en',
            'campus',
            'versions'
        )

    def get_versions(self, version):
        versions = version.offer.educationgroupversion_set.filter(transition_name=NOT_A_TRANSITION).annotate(
            is_transition=Case(
                When(transition_name='', then=Value(False)),
                default=Value(True),
                output_field=BooleanField()
            )
        )
        return MiniTrainingVersionListSerializer(versions, many=True, context=self.context).data

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if obj.version_name != '':
            data.pop('versions')
        return data
