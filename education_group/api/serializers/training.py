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

from base.models.enums import education_group_types
from education_group.api.serializers import utils
from education_group.api.serializers.education_group_year import BaseEducationGroupYearSerializer, \
    EducationGroupYearSerializer
from education_group.api.serializers.utils import VersionHyperlinkedIdentityField, FlattenMixin
from program_management.models.education_group_version import EducationGroupVersion


class TrainingListSerializer(FlattenMixin, serializers.HyperlinkedModelSerializer):
    url = VersionHyperlinkedIdentityField(read_only=True)

    management_entity = serializers.CharField(source='offer.management_entity_version.acronym', read_only=True)
    management_faculty = serializers.SerializerMethodField()
    administration_entity = serializers.CharField(source='offer.administration_entity_version.acronym', read_only=True)
    administration_faculty = serializers.SerializerMethodField()

    partial_title = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupVersion
        flatten = [('offer', BaseEducationGroupYearSerializer)]
        fields = (
            'url',
            'version_name',
            'management_entity',
            'management_faculty',
            'administration_entity',
            'administration_faculty',
            'partial_title'
        )

    @staticmethod
    def get_management_faculty(obj):
        return utils.get_entity(obj.offer, 'management')

    @staticmethod
    def get_administration_faculty(obj):
        return utils.get_entity(obj.offer, 'administration')

    def get_partial_title(self, obj):
        language = self.context.get('language')
        return getattr(
            obj,
            'partial_title' + ('_english' if language and language not in settings.LANGUAGE_CODE_FR else '')
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.education_group_type.name not in education_group_types.TrainingType.finality_types():
            data.pop('partial_title')
        return data


class TrainingDetailSerializer(TrainingListSerializer):
    class Meta(TrainingListSerializer.Meta):
        flatten = TrainingListSerializer.Meta.flatten + [('offer', EducationGroupYearSerializer)]
