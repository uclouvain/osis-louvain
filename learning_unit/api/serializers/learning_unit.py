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

from base.models.enums.summary_status import SummaryStatus
from base.models.learning_unit_year import LearningUnitYear
from learning_unit.api.serializers.campus import LearningUnitCampusSerializer
from learning_unit.api.serializers.component import LearningUnitComponentSerializer
from learning_unit.api.serializers.utils import LearningUnitHyperlinkedIdentityField, \
    LearningUnitHyperlinkedRelatedField


class LearningUnitTitleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

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
    osis_url = serializers.HyperlinkedIdentityField(
        view_name='learning_unit',
        lookup_url_kwarg="learning_unit_year_id",
        read_only=True
    )
    requirement_entity = serializers.CharField(
        source='entity_requirement',
        read_only=True
    )
    allocation_entity = serializers.CharField(
        source='entity_allocation',
        read_only=True
    )
    academic_year = serializers.IntegerField(source='academic_year.year')

    type = serializers.CharField(source='learning_container_year.container_type')
    type_text = serializers.CharField(source='get_container_type_display', read_only=True)
    subtype_text = serializers.CharField(source='get_subtype_display', read_only=True)
    has_proposal = serializers.SerializerMethodField()

    class Meta(LearningUnitTitleSerializer.Meta):
        model = LearningUnitYear
        fields = LearningUnitTitleSerializer.Meta.fields + (
            'url',
            'osis_url',
            'acronym',
            'academic_year',
            'credits',
            'status',
            'requirement_entity',
            'allocation_entity',
            'type',
            'type_text',
            'subtype',
            'subtype_text',
            'has_proposal',
        )

    def get_has_proposal(self, learning_unit_year):
        return getattr(learning_unit_year, "has_proposal", None)


class LearningUnitDetailedSerializer(LearningUnitSerializer):
    periodicity_text = serializers.CharField(source='get_periodicity_display', read_only=True)
    quadrimester_text = serializers.CharField(source='get_quadrimester_display', read_only=True)

    language = serializers.CharField(source='language.code', read_only=True)
    team = serializers.BooleanField(source='learning_container_year.team', read_only=True)

    campus = LearningUnitCampusSerializer(read_only=True)
    components = LearningUnitComponentSerializer(many=True, source='learningcomponentyear_set', read_only=True)
    parent = LearningUnitHyperlinkedRelatedField(read_only=True, lookup_field='acronym')
    partims = LearningUnitHyperlinkedRelatedField(read_only=True, many=True, source='get_partims_related')

    proposal = serializers.SerializerMethodField()
    summary_status = serializers.SerializerMethodField()

    class Meta(LearningUnitSerializer.Meta):
        model = LearningUnitYear
        fields = LearningUnitSerializer.Meta.fields + (
            'quadrimester',
            'quadrimester_text',
            'periodicity',
            'periodicity_text',
            'campus',
            'team',
            'language',
            'components',
            'parent',
            'partims',
            'proposal',
            'summary_status',
            'professional_integration'
        )

    def get_proposal(self, learning_unit_year):
        if not hasattr(learning_unit_year, "proposallearningunit"):
            return {}

        return {
            "folder": learning_unit_year.proposallearningunit.folder,
            "type": learning_unit_year.proposallearningunit.get_type_display(),
            "status": learning_unit_year.proposallearningunit.get_state_display(),
        }

    def get_summary_status(self, learning_unit_year):
        if getattr(learning_unit_year, "summary_status", False):
            return SummaryStatus.MODIFIED.value
        elif learning_unit_year.summary_locked:
            return SummaryStatus.BLOCKED.value
        return SummaryStatus.NOT_MODIFIED.value


class ExternalLearningUnitDetailedSerializer(LearningUnitDetailedSerializer):
    local_url = serializers.CharField(source='externallearningunityear.url')
    local_code = serializers.CharField(source='externallearningunityear.external_acronym')

    class Meta(LearningUnitDetailedSerializer.Meta):
        model = LearningUnitYear
        fields = LearningUnitDetailedSerializer.Meta.fields + (
            'local_code',
            'local_url'
        )
