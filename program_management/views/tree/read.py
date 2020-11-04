from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET

from program_management.ddd import command
from program_management.ddd.service.read import node_identity_service, get_program_tree_service
from program_management.serializers.program_tree_view import program_tree_view_serializer


@login_required
@require_GET
def tree_json_view(request, root_id: int):
    if request.is_ajax():
        node_identity = node_identity_service.get_node_identity_from_element_id(
            command.GetNodeIdentityFromElementId(element_id=root_id)
        )
        tree = get_program_tree_service.get_program_tree(
            command.GetProgramTree(code=node_identity.code, year=node_identity.year)
        )
        return JsonResponse(program_tree_view_serializer(tree))
    return HttpResponseBadRequest()
