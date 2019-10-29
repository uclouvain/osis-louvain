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

from base.models.admission_condition import AdmissionCondition


class DynamicLanguageFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `lang` argument that
    controls which fields should be displayed depending on the language.
    """

    def __init__(self, *args, **kwargs):
        super(DynamicLanguageFieldsModelSerializer, self).__init__(*args, **kwargs)
        language = self.context.get('lang')

        is_admission_condition = isinstance(self.instance, AdmissionCondition)
        if language is not None:
            keys_list = [
                field for field in list(self.fields.keys()) if isinstance(self.fields[field], serializers.CharField)
            ]
            for field_name in keys_list:
                source = self._get_source(field_name, is_admission_condition, language)
                # if not instance of AdmissionCondition and language is french,
                # no need to add parameter source (source = field name)
                if not language == settings.LANGUAGE_CODE_FR or is_admission_condition:
                    self.fields[field_name] = serializers.CharField(
                        source=source,
                        read_only=True
                    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in data:
            data[field] = data[field] or None
        return data

    def _get_source(self, field_name, is_admission_condition, language):
        specific_fields = ['free_text', 'text']

        prefix = 'text_' if is_admission_condition else ''

        object_source = 'common_admission_condition.' \
            if field_name not in specific_fields and is_admission_condition else ''

        field_source = self._manage_special_field_cases(field_name, is_admission_condition)

        lang = '' if language == settings.LANGUAGE_CODE_FR else '_' + language

        return object_source + prefix + field_source + lang

    def _manage_special_field_cases(self, field_name, is_admission_condition):
        field_source = 'free' if field_name == 'free_text' else field_name
        if 'section' in self.context and is_admission_condition:
            field_source = self.context.get('section')
        return field_source
