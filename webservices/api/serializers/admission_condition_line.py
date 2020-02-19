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
from django.utils import translation
from rest_framework import serializers

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from webservices.api.serializers.utils import DynamicLanguageFieldsModelSerializer


class AdmissionConditionTextsSerializer(DynamicLanguageFieldsModelSerializer):
    text = serializers.CharField(read_only=True)
    text_common = serializers.CharField(read_only=True)

    class Meta:
        model = AdmissionCondition

        fields = (
            'text',
            'text_common',
        )


class AdmissionConditionLineSerializer(DynamicLanguageFieldsModelSerializer):
    access = serializers.SerializerMethodField()

    class Meta:
        model = AdmissionConditionLine

        fields = (
            'access',
            'conditions',
            'diploma',
            'remarks'
        )

    def get_access(self, obj):
        with translation.override(self.context.get('lang')):
            return obj.get_access_display()
