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
from rest_framework.reverse import reverse

from base.models.enums.education_group_categories import Categories
from base.models.enums.learning_component_year_type import LECTURING
from education_group.api.views.group import GroupDetail
from education_group.api.views.mini_training import MiniTrainingDetail
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer_class = EducationGroupNodeTreeSerializer \
            if value.education_group_year else LearningUnitNodeTreeSerializer
        serializer = serializer_class(value, context=self.context)
        return serializer.data


class CommonNodeHyperlinkedRelatedField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        if obj.education_group_year is None:
            view_name = 'learning_unit_api_v1:' + LearningUnitDetailed.name
            url_kwargs = {
                'acronym': obj.learning_unit_year.acronym,
                'year': obj.learning_unit_year.academic_year.year,
            }
        elif obj.education_group_year.education_group_type.category == Categories.TRAINING.name:
            view_name = 'education_group_api_v1:' + TrainingDetail.name
            url_kwargs = {
                'acronym': obj.education_group_year.acronym,
                'year': obj.education_group_year.academic_year.year,
            }
        else:
            view_name = {
                Categories.GROUP.name: 'education_group_api_v1:' + GroupDetail.name,
                Categories.MINI_TRAINING.name: 'education_group_api_v1:' + MiniTrainingDetail.name
            }.get(obj.education_group_year.education_group_type.category)
            url_kwargs = {
                'partial_acronym': obj.education_group_year.partial_acronym,
                'year': obj.education_group_year.academic_year.year,
            }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class BaseCommonNodeTreeSerializer(serializers.Serializer):
    url = CommonNodeHyperlinkedRelatedField(view_name='education_group_api_v1:' + TrainingDetail.name)
    title = serializers.SerializerMethodField()
    children = RecursiveField(many=True)


class CommonNodeTreeSerializer(BaseCommonNodeTreeSerializer):
    is_mandatory = serializers.BooleanField(source='group_element_year.is_mandatory', read_only=True)
    access_condition = serializers.BooleanField(source='group_element_year.access_condition', read_only=True)
    comment = serializers.SerializerMethodField()
    link_type = serializers.CharField(source='group_element_year.link_type', read_only=True)
    link_type_text = serializers.CharField(source='group_element_year.get_link_type_display', read_only=True)
    block = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()

    @staticmethod
    def get_credits(obj):
        education_group_year = obj.education_group_year
        learning_unit_year = obj.group_element_year.child_leaf
        absolute_credits = (education_group_year and education_group_year.credits) or (
                learning_unit_year and learning_unit_year.credits
        )
        return obj.group_element_year.relative_credits or absolute_credits

    @staticmethod
    def get_block(obj):
        return sorted([int(block) for block in str(obj.group_element_year.block or '')])

    def get_comment(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.group_element_year, 'comment' + field_suffix)


class EducationGroupRootNodeTreeSerializer(BaseCommonNodeTreeSerializer):
    node_type = serializers.CharField(source='education_group_year.education_group_type.category', read_only=True)
    subtype = serializers.CharField(source='education_group_year.education_group_type.name', read_only=True)
    acronym = serializers.CharField(source='education_group_year.acronym', read_only=True)
    code = serializers.CharField(source='education_group_year.partial_acronym', read_only=True)
    remark = serializers.SerializerMethodField()
    partial_title = serializers.SerializerMethodField()
    min_constraint = serializers.IntegerField(source='education_group_year.min_constraint', read_only=True)
    max_constraint = serializers.IntegerField(source='education_group_year.max_constraint', read_only=True)
    constraint_type = serializers.CharField(source='education_group_year.constraint_type', read_only=True)

    def get_remark(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.education_group_year, 'remark' + field_suffix)

    def get_title(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.education_group_year, 'title' + field_suffix)

    def get_partial_title(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.education_group_year, 'partial_title' + field_suffix)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        node_type = data['node_type']
        if node_type != NodeType.TRAINING.name or not self.instance.education_group_year.is_finality:
            data.pop('partial_title')
        return data


class EducationGroupNodeTreeSerializer(CommonNodeTreeSerializer, EducationGroupRootNodeTreeSerializer):
    pass


class LearningUnitNodeTreeSerializer(CommonNodeTreeSerializer):
    node_type = serializers.ReadOnlyField(default=NodeType.LEARNING_UNIT.name)
    subtype = serializers.CharField(source='learning_unit_year.learning_container_year.container_type', read_only=True)
    code = serializers.CharField(source='learning_unit_year.acronym', read_only=True)
    remark = serializers.CharField(source='learning_unit_year.learning_unit.other_remark', read_only=True)
    lecturing_volume = serializers.DecimalField(max_digits=6, decimal_places=2, default=None)
    practical_exercise_volume = serializers.DecimalField(max_digits=6, decimal_places=2, default=None)
    with_prerequisite = serializers.BooleanField(source='group_element_year.has_prerequisite', read_only=True)
    periodicity = serializers.CharField(source='learning_unit_year.periodicity', read_only=True)
    quadrimester = serializers.CharField(source='learning_unit_year.quadrimester', read_only=True)
    status = serializers.BooleanField(source='learning_unit_year.status', read_only=True)
    proposal_type = serializers.SerializerMethodField()

    @staticmethod
    def get_proposal_type(obj):
        if hasattr(obj.learning_unit_year, "proposallearningunit"):
            return obj.learning_unit_year.proposallearningunit.type
        return None

    def get_title(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.learning_unit_year, 'complete_title' + field_suffix)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        for component in obj.learning_unit_year.learningcomponentyear_set.all():
            key = 'lecturing_volume' if component.type == LECTURING else 'practical_exercise_volume'
            data[key] = component.hourly_volume_total_annual
        data.pop('children')
        return data


class EducationGroupTreeSerializer(EducationGroupRootNodeTreeSerializer):
    children = RecursiveField(many=True)
