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

from base.models.learning_unit_year import LearningUnitYear
from learning_unit.api.serializers.campus import LearningUnitCampusSerializer
from learning_unit.api.serializers.component import LearningUnitComponentSerializer
from learning_unit.api.serializers.utils import LearningUnitHyperlinkedIdentityField, \
    LearningUnitHyperlinkedRelatedField


class LearningUnitTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LearningUnitYear
        fields = (
            'title',
        )

    def get_title(self, learning_unit_year):
        language = self.context['language']
        return getattr(
            learning_unit_year,
            'full_title' + ('_' + language if language not in settings.LANGUAGE_CODE_FR else '')
        )


class LearningUnitSerializer(LearningUnitTitleSerializer):
    url = LearningUnitHyperlinkedIdentityField(read_only=True)
    requirement_entity = serializers.CharField(
        source='learning_container_year.requirement_entity_version.acronym',
        read_only=True
    )
    academic_year = serializers.IntegerField(source='academic_year.year')

    type = serializers.CharField(source='learning_container_year.container_type')
    type_text = serializers.CharField(source='learning_container_year.get_container_type_display', read_only=True)
    subtype_text = serializers.CharField(source='get_subtype_display', read_only=True)

    class Meta(LearningUnitTitleSerializer.Meta):
        model = LearningUnitYear
        fields = LearningUnitTitleSerializer.Meta.fields + (
            'url',
            'acronym',
            'academic_year',
            'requirement_entity',
            'type',
            'type_text',
            'subtype',
            'subtype_text'
        )


class LearningUnitDetailedSerializer(LearningUnitSerializer):
    periodicity_text = serializers.CharField(source='get_periodicity_display', read_only=True)
    quadrimester_text = serializers.CharField(source='get_quadrimester_display', read_only=True)

    language = serializers.CharField(source='language.code', read_only=True)
    team = serializers.BooleanField(source='learning_container_year.team', read_only=True)

    campus = LearningUnitCampusSerializer(read_only=True)
    components = LearningUnitComponentSerializer(many=True, source='learningcomponentyear_set', read_only=True)

    parent = LearningUnitHyperlinkedRelatedField(read_only=True, lookup_field='acronym')
    partims = LearningUnitHyperlinkedRelatedField(read_only=True, many=True, source='get_partims_related')

    class Meta(LearningUnitSerializer.Meta):
        model = LearningUnitYear
        fields = LearningUnitSerializer.Meta.fields + (
            'credits',
            'status',
            'quadrimester',
            'quadrimester_text',
            'periodicity',
            'periodicity_text',
            'campus',
            'team',
            'language',
            'components',
            'parent',
            'partims'
        )
