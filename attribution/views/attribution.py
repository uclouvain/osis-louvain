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
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from attribution.business import attribution_json


class RecomputePortalSerializer(serializers.Serializer):
    global_ids = serializers.ListField(child=serializers.CharField(), required=False)


@api_view(['POST'])
def recompute_portal(request):
    serializer = RecomputePortalSerializer(data=request.data)
    if serializer.is_valid():
        global_ids = serializer.data['global_ids'] if serializer.data['global_ids'] else None
        result = attribution_json.publish_to_portal(global_ids)
        if result:
            return Response(status=status.HTTP_202_ACCEPTED)
    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

