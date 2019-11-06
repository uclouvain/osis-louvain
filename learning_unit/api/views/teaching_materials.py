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
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from base.models.learning_unit_year import LearningUnitYear
from base.models.teaching_material import TeachingMaterial
from learning_unit.api.serializers.teaching_materials import LearningUnitTeachingMaterialSerializer


class LearningUnitTeachingMaterials(generics.ListAPIView):
    """
        Return all teaching materials of the learning unit specified
    """
    name = 'learningunitteachingmaterials_read'
    filter_backends = []
    paginator = None
    serializer_class = LearningUnitTeachingMaterialSerializer

    def get_queryset(self):
        luy = get_object_or_404(
            LearningUnitYear.objects.all(),
            acronym__iexact=self.kwargs['acronym'],
            academic_year__year=self.kwargs['year']
        )
        return TeachingMaterial.objects.filter(learning_unit_year=luy).order_by('order')
