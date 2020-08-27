import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_common.decorators.ajax import ajax_required
from program_management.ddd.command import GetLastExistingVersionNameCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.service.read import get_last_existing_version_service


@login_required
@ajax_required
@require_http_methods(['GET'])
def check_version_name(request, year, code):
    version_name = request.GET['version_name']
    existed_version_name = False
    existing_version = __get_last_existing_version(version_name, year, code)
    last_using = None
    if existing_version and existing_version.year < year:
        last_using = display_as_academic_year(existing_version.year)
        existed_version_name = True
    valid = bool(re.match("^[A-Z]{0,15}$", request.GET['version_name'].upper()))
    return JsonResponse({
        "existed_version_name": existed_version_name,
        "existing_version_name": bool(existing_version and existing_version.year >= year),
        "last_using": last_using,
        "valid": valid,
        "version_name": request.GET['version_name']}, safe=False)


def __get_last_existing_version(version_name: str, year: int, offer_acronym: str) -> ProgramTreeVersionIdentity:
    return get_last_existing_version_service.get_last_existing_version_identity(
        GetLastExistingVersionNameCommand(
            version_name=version_name,
            offer_acronym=offer_acronym,
            is_transition=False,
        )
    )
