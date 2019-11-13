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
from rest_framework import serializers

from attribution.models.attribution_new import AttributionNew
from base.models.person import Person


class PersonAttributionSerializer(serializers.ModelSerializer):
    global_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    middle_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)

    class Meta:
        model = Person
        fields = (
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'global_id'
        )


class LearningUnitAttributionSerializer(PersonAttributionSerializer):
    function_text = serializers.CharField(source='get_function_display', read_only=True)
    substitute = PersonAttributionSerializer(read_only=True)

    class Meta:
        model = AttributionNew
        fields = PersonAttributionSerializer.Meta.fields + (
            'function',
            'function_text',
            'substitute'
        )
