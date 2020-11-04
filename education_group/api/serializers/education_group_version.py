##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from education_group.api.serializers.utils import TrainingHyperlinkedIdentityField, MiniTrainingHyperlinkedIdentityField
from program_management.models.education_group_version import EducationGroupVersion


class VersionListSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='root_group.partial_acronym', read_only=True)

    class Meta:
        model = EducationGroupVersion
        fields = (
            'url',
            'version_name',
            'code',
            'is_transition'
        )


class TrainingVersionListSerializer(VersionListSerializer):
    url = TrainingHyperlinkedIdentityField(read_only=True)


class MiniTrainingVersionListSerializer(VersionListSerializer):
    url = MiniTrainingHyperlinkedIdentityField(read_only=True)
