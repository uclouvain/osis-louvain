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
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base.views.common import display_error_messages, display_success_messages
from program_management.ddd import command as command_program_management
from program_management.ddd.domain.exception import ProgramTreeNotFoundException
from program_management.ddd.service.write.publish_program_trees_using_node_service import PublishNodesException
from program_management.ddd.service.read import get_program_tree_service
from program_management.ddd.service.write import publish_program_trees_using_node_service


@login_required
@require_http_methods(['POST'])
def publish(request, year, code):
    try:
        program_tree = get_program_tree_service.get_program_tree(
            command_program_management.GetProgramTree(code=code, year=year)
        )

        cmd = command_program_management.PublishProgramTreesVersionUsingNodeCommand(
            code=program_tree.root_node.code, year=program_tree.root_node.year
        )
        publish_program_trees_using_node_service.publish_program_trees_using_node(cmd)
        message = _("The program %(title)s - %(academic_year)s will be published soon") % {
            'title': program_tree.root_node.title,
            'academic_year': program_tree.root_node.academic_year
        }
        display_success_messages(request, message)
    except ProgramTreeNotFoundException:
        raise Http404
    except PublishNodesException as e:
        display_error_messages(request, e.message)

    if program_tree.root_node.is_training():
        url_name = 'training_general_information'
    elif program_tree.root_node.is_mini_training():
        url_name = 'mini_training_general_information'
    else:
        url_name = 'group_general_information'
    default_redirect_view = reverse(url_name, kwargs={'year': year, 'code': code})
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', default_redirect_view))
