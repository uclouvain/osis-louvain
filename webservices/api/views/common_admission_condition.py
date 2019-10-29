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
from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response

from base.business.education_groups import general_information_sections
from base.models.education_group_year import EducationGroupYear
from webservices.api.serializers.common_admission_condition import CommonAdmissionConditionSerializer


class CommonAdmissionCondition(generics.RetrieveAPIView):
    """
        Return the common admission conditions for Education Group Years
    """
    name = 'commonadmissionconditions_read'
    serializer_class = CommonAdmissionConditionSerializer

    def get(self, request, *args, **kwargs):
        commons_qs = EducationGroupYear.objects.look_for_common(
            academic_year__year=self.kwargs['year'],
            education_group_type__name__in=general_information_sections.COMMON_TYPE_ADMISSION_CONDITIONS.keys(),
            acronym__contains='common-'
        ).select_related('admissioncondition', 'education_group_type')
        if not commons_qs.exists():
            raise Http404
        language = self.kwargs['language']
        common_admission_condition = {}
        suffix_language = '' if language == settings.LANGUAGE_CODE_FR[:2] else '_en'
        for common in commons_qs:
            relevant_attr = general_information_sections.COMMON_TYPE_ADMISSION_CONDITIONS[
                common.education_group_type.name
            ]
            common_admission_condition[common.acronym] = {
                field: self._get_value_from_ac(common.admissioncondition, field, suffix_language)
                for field in relevant_attr
            }

        serializer = self.get_serializer(common_admission_condition)
        return Response(serializer.data)

    @staticmethod
    def _get_value_from_ac(admission_condition, field, suffix_language):
        return getattr(admission_condition, 'text_{}{}'.format(field, suffix_language)) or None
