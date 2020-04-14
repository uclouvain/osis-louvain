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

from base.api.serializers.campus import CampusDetailSerializer
from education_group.api.serializers import utils
from education_group.api.serializers.education_group_year import BaseEducationGroupYearSerializer
from education_group.api.serializers.utils import MiniTrainingHyperlinkedIdentityField, FlattenMixin
from program_management.models.education_group_version import EducationGroupVersion


class MiniTrainingListSerializer(FlattenMixin, serializers.ModelSerializer):
    url = MiniTrainingHyperlinkedIdentityField(read_only=True)
    code = serializers.CharField(source='root_group.partial_acronym')
    management_entity = serializers.CharField(source='offer.management_entity_version.acronym', read_only=True)
    management_faculty = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupVersion
        flatten = [('offer', BaseEducationGroupYearSerializer)]
        fields = (
            'url',
            'code',
            'management_entity',
            'management_faculty',
        )

    @staticmethod
    def get_management_faculty(obj):
        return utils.get_entity(obj.offer, 'management')


class MiniTrainingDetailSerializer(MiniTrainingListSerializer):
    remark = serializers.SerializerMethodField()
    campus = CampusDetailSerializer(source='offer.main_teaching_campus', read_only=True)
    schedule_type = serializers.CharField(source='offer.schedule_type', read_only=True)
    min_constraint = serializers.CharField(source='offer.min_constraint', read_only=True)
    max_constraint = serializers.CharField(source='offer.max_constraint', read_only=True)
    constraint_type = serializers.CharField(source='offer.constraint_type', read_only=True)
    active = serializers.CharField(source='offer.active', read_only=True)
    keywords = serializers.CharField(source='offer.keywords', read_only=True)

    # Display human readable value
    constraint_type_text = serializers.CharField(source='offer.get_constraint_type_display', read_only=True)
    active_text = serializers.CharField(source='offer.get_active_display', read_only=True)
    schedule_type_text = serializers.CharField(source='offer.get_schedule_type_display', read_only=True)
    credits = serializers.IntegerField(source='root_group.credits', read_only=True)

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
            'campus',
        )

    def get_remark(self, version):
        language = self.context.get('language')
        return getattr(
            version.offer,
            'remark' + ('_english' if language and language not in settings.LANGUAGE_CODE_FR else '')
        )
