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
from django.views.decorators.http import require_http_methods

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_common.decorators.ajax import ajax_required
from program_management.ddd import command
from program_management.ddd.service.read import check_transition_name_service


@login_required
@ajax_required
@require_http_methods(['GET'])
def check_transition_name(request, year, acronym):
    transition_name = request.GET['transition_name']
    cmd = command.CheckTransitionNameCommand(
        year=year,
        offer_acronym=acronym,
        transition_name=transition_name
    )

    try:
        check_transition_name_service.check_transition_name(cmd)
    except MultipleBusinessExceptions as multiple_exceptions:
        first_exception = next(e for e in multiple_exceptions.exceptions)
        return JsonResponse({
            "valid": False,
            "msg": first_exception.message
        })
    return JsonResponse({
        "valid": True,
        "msg": None
    })
