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
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics

from attribution.models.attribution_charge_new import AttributionChargeNew
from base.models.learning_unit_year import LearningUnitYear
from learning_unit.api.serializers.attribution import LearningUnitAttributionSerializer


class LearningUnitAttribution(generics.ListAPIView):
    """
        Return the attributions of the learning unit
    """
    name = 'learningunitattributions_read'
    serializer_class = LearningUnitAttributionSerializer
    filter_backends = []
    paginator = None

    def get_queryset(self):
        luy = get_object_or_404(
            LearningUnitYear.objects.all(),
            acronym__iexact=self.kwargs['acronym'],
            academic_year__year=self.kwargs['year']
        )
        return AttributionChargeNew.objects.select_related(
            'learning_component_year__learning_unit_year',
            'attribution__tutor__person',
            'attribution__substitute'
        ).filter(
            learning_component_year__learning_unit_year=luy
        ).distinct(
            'attribution__tutor'
        ).annotate(
            first_name=F('attribution__tutor__person__first_name'),
            middle_name=F('attribution__tutor__person__middle_name'),
            last_name=F('attribution__tutor__person__last_name'),
            email=F('attribution__tutor__person__email'),
            global_id=F('attribution__tutor__person__global_id'),
        )
