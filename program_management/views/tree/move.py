##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from waffle.decorators import waffle_flag

import program_management.ddd.service.write.down_link_service
import program_management.ddd.service.write.up_link_service
from base.views.common import display_success_messages
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import permission_required
from program_management.ddd import command, service
from program_management.ddd.repositories import node as node_repository
from program_management.ddd.domain import node


def group_element_year_parent_getter_via_path(request) -> GroupYear:
    path = request.POST["path"]
    *_, parent_id, child_id = path.split("|")
    return get_object_or_404(GroupYear, element__id=parent_id)


@login_required
@waffle_flag("education_group_update")
@permission_required("base.change_link_data", fn=group_element_year_parent_getter_via_path)
@require_http_methods(['POST'])
def up(request):
    path = request.POST["path"]
    command_up = command.OrderUpLinkCommand(path=path)
    node_identity_id = service.write.up_link_service.up_link(command_up)

    moved_node = node_repository.NodeRepository.get(
        node.NodeIdentity(node_identity_id.code, node_identity_id.year)
    )
    success_msg = _("The %(year)s - %(acronym)s%(title)s has been moved") % {'acronym': node_identity_id.code,
                                                                             'year': node_identity_id.year,
                                                                             'title': " - {}".format(moved_node.title)
                                                                             if moved_node and moved_node.title else ""}
    display_success_messages(request, success_msg)

    http_referer = request.META.get('HTTP_REFERER')
    return redirect(http_referer)


@login_required
@waffle_flag("education_group_update")
@permission_required("base.change_link_data", fn=group_element_year_parent_getter_via_path)
@require_http_methods(['POST'])
def down(request):
    path = request.POST["path"]
    command_down = command.OrderDownLinkCommand(path=path)
    node_identity_id = service.write.down_link_service.down_link(command_down)

    moved_node = node_repository.NodeRepository.get(
        node.NodeIdentity(node_identity_id.code, node_identity_id.year)
    )

    success_msg = _("The %(year)s - %(acronym)s%(title)s has been moved") % {'acronym': node_identity_id.code,
                                                                             'year': node_identity_id.year,
                                                                             'title': " - {}".format(moved_node.title)
                                                                             if moved_node and moved_node.title else ""}
    display_success_messages(request, success_msg)

    http_referer = request.META.get('HTTP_REFERER')
    return redirect(http_referer)
