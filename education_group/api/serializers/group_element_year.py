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

from education_group.api.views.group import GroupDetail
from education_group.api.views.mini_training import MiniTrainingDetail
from education_group.api.views.training import TrainingDetail
from education_group.enums.node_type import NodeType
from learning_unit.api.views.learning_unit import LearningUnitDetailed
from program_management.ddd.business_types import *


class RecursiveField(serializers.Serializer):
    def to_representation(self, value: 'Link'):
        if value.is_link_with_learning_unit():
            return LearningUnitNodeTreeSerializer(value, context=self.context).data
        return EducationGroupNodeTreeSerializer(value, context=self.context).data


class CommonNodeHyperlinkedRelatedField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj: 'Link', view_name, request, format):
        if obj.is_link_with_learning_unit():
            view_name = 'learning_unit_api_v1:' + LearningUnitDetailed.name
            url_kwargs = {
                'acronym': obj.child.code,
                'year': obj.child.year,
            }
        elif obj.child.is_training():
            view_name = 'education_group_api_v1:' + TrainingDetail.name
            url_kwargs = {
                'acronym': obj.child.title,
                'year': obj.child.year,
            }
        else:
            view_name = 'education_group_api_v1:' + GroupDetail.name
            url_kwargs = {
                'year': obj.child.year,
                'partial_acronym': obj.child.code,
            }
            if obj.child.is_mini_training():
                view_name = 'education_group_api_v1:' + MiniTrainingDetail.name
                url_kwargs = {
                    'year': obj.child.year,
                    'official_partial_acronym': obj.child.code,
                }

        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class BaseCommonNodeTreeSerializer(serializers.Serializer):
    url = CommonNodeHyperlinkedRelatedField(view_name='education_group_api_v1:' + TrainingDetail.name)
    title = serializers.SerializerMethodField()
    children = RecursiveField(
        source='child.get_children_and_only_reference_children_except_within_minor_list',
        many=True
    )


class CommonNodeTreeSerializer(BaseCommonNodeTreeSerializer):
    is_mandatory = serializers.BooleanField(read_only=True)
    access_condition = serializers.BooleanField(read_only=True)
    comment = serializers.SerializerMethodField()
    link_type = serializers.CharField(source='link_type.name', allow_null=True, read_only=True)
    link_type_text = serializers.CharField(source='link_type.value', allow_null=True, read_only=True)
    block = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()

    @staticmethod
    def get_credits(obj: 'Link'):
        absolute_credits = obj.child.credits
        return obj.relative_credits or absolute_credits or None

    @staticmethod
    def get_block(obj: 'Link'):
        return sorted([int(block) for block in str(obj.block or '')])

    def get_comment(self, obj: 'Link'):
        field_suffix = '_english' if self.context.get('language') == settings.LANGUAGE_CODE_EN else ''
        return getattr(obj, 'comment' + field_suffix)


class EducationGroupCommonNodeTreeSerializer(serializers.Serializer):
    node_type = serializers.SerializerMethodField(read_only=True)
    subtype = serializers.CharField(source='child.node_type.name', read_only=True)
    acronym = serializers.CharField(source='child.title', read_only=True)
    code = serializers.CharField(source='child.code', read_only=True)
    remark = serializers.SerializerMethodField()
    partial_title = serializers.SerializerMethodField()
    min_constraint = serializers.IntegerField(source='child.min_constraint', read_only=True)
    max_constraint = serializers.IntegerField(source='child.max_constraint', read_only=True)
    constraint_type = serializers.CharField(source='child.constraint_type', read_only=True)

    @staticmethod
    def get_node_type(obj):
        if obj.child.is_training():
            return NodeType.TRAINING.name
        elif obj.child.is_mini_training():
            return NodeType.MINI_TRAINING.name
        else:
            return NodeType.GROUP.name

    def get_remark(self, obj):
        field_suffix = '_en' if self.context.get('language') == settings.LANGUAGE_CODE_EN else '_fr'
        return getattr(obj.child, 'remark' + field_suffix)

    def get_title(self, obj):
        field_suffix = 'en' if self.context.get('language') == settings.LANGUAGE_CODE_EN else 'fr'
        field_prefix = 'offer' if obj.child.is_training() else 'group'
        return getattr(obj.child, '{}_title_{}'.format(field_prefix, field_suffix))

    def get_partial_title(self, obj):
        field_suffix = '_en' if self.context.get('language') == settings.LANGUAGE_CODE_EN else '_fr'
        return getattr(obj.child, 'offer_partial_title' + field_suffix)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if not obj.child.is_training() or not self.instance.child.is_finality():
            data.pop('partial_title')
        return data


class EducationGroupRootNodeTreeSerializer(BaseCommonNodeTreeSerializer, EducationGroupCommonNodeTreeSerializer):
    acronym = serializers.SerializerMethodField(read_only=True)

    def get_acronym(self, obj):
        version_name = self.context.get('version_name')
        return obj.child.title + ('[{}]'.format(version_name) if version_name else '')

    def get_title(self, obj):
        field_suffix = '_en' if self.context.get('language') == settings.LANGUAGE_CODE_EN else '_fr'
        version_title = self.context.get('version_title' + field_suffix)
        title_suffix = ' [{}]'.format(version_title) if version_title else ''
        title = getattr(obj.child, 'offer_title' + field_suffix)
        return title + title_suffix if title else None


class EducationGroupNodeTreeSerializer(CommonNodeTreeSerializer, EducationGroupCommonNodeTreeSerializer):
    pass


class LearningUnitNodeTreeSerializer(CommonNodeTreeSerializer):
    node_type = serializers.ReadOnlyField(default=NodeType.LEARNING_UNIT.name)
    subtype = serializers.CharField(source='child.learning_unit_type.name', read_only=True)
    code = serializers.CharField(source='child.code', read_only=True)
    remark = serializers.CharField(source='child.other_remark', read_only=True)
    lecturing_volume = serializers.DecimalField(
        source='child.volume_total_lecturing',
        max_digits=6,
        decimal_places=2,
        default=None
    )
    practical_exercise_volume = serializers.DecimalField(
        source='child.volume_total_practical',
        max_digits=6,
        decimal_places=2,
        default=None
    )
    with_prerequisite = serializers.BooleanField(source='child.has_prerequisite', read_only=True)
    periodicity = serializers.CharField(source='child.periodicity.name', allow_null=True, read_only=True)
    quadrimester = serializers.CharField(source='child.quadrimester.name', allow_null=True, read_only=True)
    status = serializers.BooleanField(source='child.status', read_only=True)
    proposal_type = serializers.CharField(source='child.proposal_type.name', allow_null=True, read_only=True)

    def get_title(self, obj: 'Link'):
        if self.context.get('language') == settings.LANGUAGE_CODE_EN:
            specific_title = obj.child.specific_title_en
            common_title = obj.child.common_title_en
        else:
            specific_title = obj.child.specific_title_fr
            common_title = obj.child.common_title_fr

        complete_title = specific_title
        if common_title:
            complete_title = common_title + (' - ' + specific_title if specific_title else "")
        return complete_title

    def to_representation(self, obj: 'Link'):
        data = super().to_representation(obj)
        data.pop('children')
        return data
