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
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from base.models.education_group_year import EducationGroupYear
from cms.models.translated_text import TranslatedText
from webservices.api.serializers.common_text import CommonTextSerializer


class CommonText(generics.RetrieveAPIView):
    """
        Return the common general informations for Education Group Years
    """
    name = 'commontexts_read'
    serializer_class = CommonTextSerializer

    def get(self, request, *args, **kwargs):
        language = self.kwargs['language']
        egy = get_object_or_404(
            EducationGroupYear.objects.select_related(
                'academic_year',
            ),
            acronym='common',
            academic_year__year=self.kwargs['year']
        )
        texts = TranslatedText.objects.filter(
            reference=egy.id,
            language=language if language != settings.LANGUAGE_CODE_FR[:2] else settings.LANGUAGE_CODE_FR
        ).select_related('text_label')
        common_texts = {}
        for text in texts:
            common_texts[text.text_label.label] = text.text
        serializer = self.get_serializer(common_texts)
        return Response(serializer.data)
