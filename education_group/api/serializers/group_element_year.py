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
from education_group.api.views.group import GroupDetail
from education_group.api.views.mini_training import MiniTrainingDetail
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
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


class CommonNodeTreeSerializer(serializers.Serializer):
    url = CommonNodeHyperlinkedRelatedField(view_name='education_group_api_v1:' + TrainingDetail.name)
    acronym = serializers.SerializerMethodField()
    code = serializers.CharField(source='education_group_year.partial_acronym', read_only=True)
    title = serializers.SerializerMethodField()
    node_type = serializers.SerializerMethodField()

    def get_node_type(self, obj):
        if obj.education_group_year is None:
            return NodeType.LEARNING_UNIT.name
        return obj.education_group_year.education_group_type.category

    def get_acronym(self, obj):
        if self.get_node_type(obj) == NodeType.LEARNING_UNIT.name:
            return obj.learning_unit_year.acronym
        return obj.education_group_year.acronym

    def get_title(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        if self.get_node_type(obj) == NodeType.LEARNING_UNIT.name:
            return getattr(obj.learning_unit_year, 'complete_title' + field_suffix)
        return getattr(obj.education_group_year, 'title' + field_suffix)


class NodeTreeSerializer(CommonNodeTreeSerializer):
    relative_credits = serializers.IntegerField(source='group_element_year.relative_credits', read_only=True)
    is_mandatory = serializers.BooleanField(source='group_element_year.is_mandatory', read_only=True)
    access_condition = serializers.BooleanField(source='group_element_year.access_condition', read_only=True)
    comment = serializers.SerializerMethodField()
    link_type = serializers.CharField(source='group_element_year.link_type', read_only=True)
    link_type_text = serializers.CharField(source='group_element_year.get_link_type_display', read_only=True)
    block = serializers.SerializerMethodField()
    children = RecursiveField(many=True)

    def get_block(self, obj):
        return sorted([int(block) for block in str(obj.group_element_year.block or '')])

    def get_comment(self, obj):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj.group_element_year, 'comment' + field_suffix)


class EducationGroupTreeSerializer(CommonNodeTreeSerializer):
    children = NodeTreeSerializer(many=True)
