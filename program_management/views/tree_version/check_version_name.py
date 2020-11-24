from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_common.decorators.ajax import ajax_required
from program_management.ddd import command
from program_management.ddd.domain.exception import VersionNameExistedException
from program_management.ddd.service.read import check_version_name_service


@login_required
@ajax_required
@require_http_methods(['GET'])
def check_version_name(request, year, acronym):
    version_name = request.GET['version_name']
    cmd = command.CheckVersionNameCommand(year=year, offer_acronym=acronym, version_name=version_name)

    try:
        check_version_name_service.check_version_name(cmd)
    except MultipleBusinessExceptions as multiple_exceptions:
        first_exception = next(e for e in multiple_exceptions.exceptions)
        if isinstance(first_exception, VersionNameExistedException):
            return JsonResponse({
                "valid": True,
                "msg": first_exception.message
            })

        return JsonResponse({
            "valid": False,
            "msg": first_exception.message
        })
    return JsonResponse({
        "valid": True,
        "msg": None
    })
