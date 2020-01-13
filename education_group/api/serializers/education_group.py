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
from rest_framework.reverse import reverse

from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from education_group.api.views.group import GroupDetail
from education_group.api.views.mini_training import MiniTrainingDetail
from education_group.api.views.training import TrainingDetail


class EducationGroupHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    def __init__(self, *args, **kwargs):
        super().__init__(view_name='education_group_read', **kwargs)

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'root_id': obj.pk,
            'education_group_year_id': obj.pk
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class EducationGroupSerializer(serializers.HyperlinkedModelSerializer):
    url = EducationGroupHyperlinkedIdentityField()
    code = serializers.CharField(source='partial_acronym')
    academic_year = serializers.StringRelatedField()
    education_group_type = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EducationGroupType.objects.all(),
    )
    management_entity = serializers.CharField(source='management_entity_version.acronym', read_only=True, default='')

    # Display human readable value
    education_group_type_text = serializers.CharField(source='education_group_type.get_name_display', read_only=True)

    class Meta:
        model = EducationGroupYear
        fields = (
            'url',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'title',
            'academic_year',
            'management_entity',
        )


class EducationGroupYearHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    default_view = 'education_group_api_v1:' + TrainingDetail.name

    lookup_field = None

    def __init__(self, lookup_field=None, **kwargs):
        self.lookup_field = lookup_field or ''
        super().__init__(view_name=self.default_view, **kwargs)

    def _get_view_name(self, category):
        return {
            Categories.TRAINING.name: self.default_view,
            Categories.MINI_TRAINING.name: 'education_group_api_v1:' + MiniTrainingDetail.name,
            Categories.GROUP.name: 'education_group_api_v1:' + GroupDetail.name,
        }[category]

    @staticmethod
    def _get_view_kwargs(education_group_year):
        acronym_key = {
            Categories.TRAINING.name: 'acronym',
            Categories.MINI_TRAINING.name: 'partial_acronym',
            Categories.GROUP.name: 'partial_acronym',
        }[education_group_year.education_group_type.category]
        acronym_value = getattr(education_group_year, acronym_key, education_group_year)
        return {
            acronym_key: acronym_value,
            'year': education_group_year.academic_year.year
        }

    def get_url(self, obj, view_name, request, format):
        education_group_year = obj
        for attr in self.lookup_field.split('__'):
            education_group_year = getattr(education_group_year, attr, education_group_year)

        category = education_group_year.education_group_type.category

        return reverse(
            self._get_view_name(category),
            kwargs=self._get_view_kwargs(education_group_year),
            request=request,
            format=format
        )
