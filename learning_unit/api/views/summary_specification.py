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
from django.db.models import F, Q
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from base.business.learning_unit import CMS_LABEL_PEDAGOGY, CMS_LABEL_SPECIFICATIONS, CMS_LABEL_PEDAGOGY_FR_AND_EN, \
    CMS_LABEL_PEDAGOGY_FR_ONLY
from base.models.learning_unit_year import LearningUnitYear
from cms.models.translated_text import TranslatedText
from learning_unit.api.serializers.summary_specification import LearningUnitSummarySpecificationSerializer


class LearningUnitSummarySpecification(generics.GenericAPIView):
    """
        Return all summary and specification information of the learning unit specified
    """
    name = 'learningunitsummaryspecification_read'
    filter_backends = []
    paginator = None
    serializer_class = LearningUnitSummarySpecificationSerializer

    def get(self, request, *args, **kwargs):
        learning_unit_year = get_object_or_404(
            LearningUnitYear.objects.all(),
            acronym__iexact=self.kwargs['acronym'],
            academic_year__year=self.kwargs['year']
        )
        parent = learning_unit_year.parent
        qs_parent = self._get_translated_texts(parent) if parent else None
        qs = self._get_translated_texts(learning_unit_year).values('label', 'text')

        summary_specification_grouped = dict.fromkeys(CMS_LABEL_PEDAGOGY + CMS_LABEL_SPECIFICATIONS, None)
        for key in summary_specification_grouped.keys():
            partim_text = qs.filter(label=key).values_list('text', flat=True).first()
            parent_text = qs_parent.filter(label=key).values_list('text', flat=True).first() if qs_parent else None
            summary_specification_grouped[key] = partim_text if partim_text else parent_text

        serializer = self.get_serializer(summary_specification_grouped)

        return Response(serializer.data)

    def _get_translated_texts(self, luy):
        language = self.request.LANGUAGE_CODE
        qs = TranslatedText.objects.filter(
            reference=luy.pk,
            text_label__label__in=CMS_LABEL_PEDAGOGY + CMS_LABEL_SPECIFICATIONS
        ).annotate(
            label=F('text_label__label')
        ).filter(
            Q(
                language=settings.LANGUAGE_CODE_FR if language == settings.LANGUAGE_CODE_FR[:2] else language,
                label__in=CMS_LABEL_PEDAGOGY_FR_AND_EN + CMS_LABEL_SPECIFICATIONS
            )
            |
            Q(
                language=settings.LANGUAGE_CODE_FR,
                label__in=CMS_LABEL_PEDAGOGY_FR_ONLY
            )
        )
        return qs
