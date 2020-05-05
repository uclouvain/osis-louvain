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
from rest_framework import generics

from backoffice.settings.rest_framework.common_views import LanguageContextSerializerMixin
from base.models.hops import Hops
from education_group.api.serializers.hops import HopsListSerializer


class HopsList(LanguageContextSerializerMixin, generics.RetrieveAPIView):
    """
        Return the list of used habilitation
    """
    name = 'habilitations_list'
    serializer_class = HopsListSerializer

    def get_object(self):
        year = self.kwargs['year']
        hops = Hops.objects.filter(
            education_group_year__academic_year__year=year
        ).values_list('ares_ability', flat=True).distinct()
        return hops
