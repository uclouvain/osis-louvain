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
from rest_framework import views
from rest_framework.response import Response

from base.api.models.program_manager_check import CheckAccessToStudent
from base.api.serializers.program_manager_check import CheckAccessToStudentSerializer
from base.business.program_manager import program_manager_check as pm_business


class AccessToStudentView(views.APIView):

    name = 'check-program-manager'
    http_method_names = ['get']

    def get(self, request, global_id, registration_id):
        results = CheckAccessToStudentSerializer(CheckAccessToStudent(global_id, registration_id, pm_business.checkAccessToStudent(global_id, registration_id)))
        return Response(results.data)
