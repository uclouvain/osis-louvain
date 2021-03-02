##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.models.campus import Campus
from base.models.entity_version_address import EntityVersionAddress
from base.views.learning_units.search.common import BaseLearningUnitSearch, SearchTypes
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer
from osis_common.decorators.ajax import ajax_required
from base.utils.search import RenderToExcel
from base.views.learning_units.search.common import _create_xls_external_ue_with_parameters


@RenderToExcel("xls_with_parameters", _create_xls_external_ue_with_parameters)
class ExternalLearningUnitSearch(BaseLearningUnitSearch):
    template_name = "learning_unit/search/external.html"
    search_type = SearchTypes.EXTERNAL_SEARCH
    filterset_class = ExternalLearningUnitFilter
    serializer_class = LearningUnitDetailedSerializer
    permission_required = "base.can_access_externallearningunityear"


@login_required
@ajax_required
def get_cities_related_to_country(request):
    """ Ajax request to get city list according to country provided"""
    country = request.GET.get('country')
    cities = []
    if country:
        cities = EntityVersionAddress.objects.filter(
            country=country
        ).distinct('city').order_by('city').values('city')
    return JsonResponse(list(cities), safe=False)


@login_required
@ajax_required
def get_campuses_related_to_city(request):
    """ Ajax request to get campus list according to city provided """
    city = request.GET.get('city')
    campuses = Campus.objects.filter(
        organization__entity__entityversion__entityversionaddress__city=city,
        organization__entity__entityversion__parent__isnull=True
    ).distinct('organization__name').order_by('organization__name').values('pk', 'organization__name')
    return JsonResponse(list(campuses), safe=False)
