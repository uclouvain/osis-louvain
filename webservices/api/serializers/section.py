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
from rest_framework import serializers

from base.models.admission_condition import AdmissionCondition
from base.models.enums.education_group_types import TrainingType
from webservices.api.serializers.achievement import AchievementsSerializer
from webservices.api.serializers.admission_condition import AdmissionConditionsSerializer, \
    BachelorAdmissionConditionsSerializer, SpecializedMasterAdmissionConditionsSerializer, \
    AggregationAdmissionConditionsSerializer, MasterAdmissionConditionsSerializer, \
    ContinuingEducationTrainingAdmissionConditionsSerializer
from webservices.api.serializers.contacts import ContactsSerializer


class SectionSerializer(serializers.Serializer):
    id = serializers.CharField(source='label', read_only=True)
    label = serializers.CharField(source='translated_label', read_only=True)
    content = serializers.CharField(source='text', read_only=True, allow_null=True)

    class Meta:
        fields = (
            'id',
            'label',
            'content',
        )


class AchievementSectionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    label = serializers.CharField(source='id', read_only=True)
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        egy = self.context.get('egy')
        return AchievementsSerializer(egy, context=self.context).data


class AdmissionConditionSectionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    label = serializers.CharField(source='id', read_only=True)
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        # FIXME: Bachelor has no admissioncondition
        admission_condition_serializers = {
            TrainingType.BACHELOR.name: BachelorAdmissionConditionsSerializer,
            TrainingType.MASTER_MC.name: SpecializedMasterAdmissionConditionsSerializer,
            TrainingType.AGGREGATION.name: AggregationAdmissionConditionsSerializer,
            TrainingType.PGRM_MASTER_120.name: MasterAdmissionConditionsSerializer,
            TrainingType.PGRM_MASTER_180_240.name: MasterAdmissionConditionsSerializer,
            TrainingType.MASTER_M1.name: MasterAdmissionConditionsSerializer,
            TrainingType.CERTIFICATE_OF_PARTICIPATION.name: ContinuingEducationTrainingAdmissionConditionsSerializer,
            TrainingType.CERTIFICATE_OF_SUCCESS.name: ContinuingEducationTrainingAdmissionConditionsSerializer,
            TrainingType.CERTIFICATE_OF_HOLDING_CREDITS.name: ContinuingEducationTrainingAdmissionConditionsSerializer,
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name:
                ContinuingEducationTrainingAdmissionConditionsSerializer,
            TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name:
                ContinuingEducationTrainingAdmissionConditionsSerializer,
        }
        serializer = admission_condition_serializers.get(
            self.get_education_group_year().education_group_type.name,
            AdmissionConditionsSerializer,
        )
        return serializer(self.get_admission_condition(), context=self.context).data

    def get_education_group_year(self):
        return self.context['egy']

    def get_admission_condition(self):
        try:
            return self.get_education_group_year().admissioncondition
        except AdmissionCondition.DoesNotExist:
            return AdmissionCondition.objects.create(education_group_year=self.get_education_group_year())


class ContactsSectionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    label = serializers.CharField(source='id', read_only=True)
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        egy = self.context.get('egy')
        return ContactsSerializer(egy, context=self.context).data
