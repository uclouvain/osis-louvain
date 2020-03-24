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

from base.models.education_group_type import EducationGroupType


class EducationGroupHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        super().__init__(view_name='education_group_read', **kwargs)

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'root_id': obj.pk,
            'education_group_year_id': obj.pk
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class EducationGroupSerializer(serializers.Serializer):
    url = EducationGroupHyperlinkedIdentityField()
    code = serializers.CharField(source='partial_acronym')
    academic_year = serializers.StringRelatedField()
    education_group_type = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EducationGroupType.objects.all(),
    )
    management_entity = serializers.StringRelatedField()
    complete_title_fr = serializers.CharField()
    title = serializers.CharField()

    # Display human readable value
    education_group_type_text = serializers.CharField(source='education_group_type.get_name_display', read_only=True)

    class Meta:
        fields = (
            'url',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
            'management_entity'
        )
