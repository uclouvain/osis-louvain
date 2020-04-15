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
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from waffle.decorators import waffle_flag

from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache
from base.views.common import display_success_messages
from base.views.education_groups import perms
from base.views.education_groups.select import get_clipboard_content_display, build_success_json_response
from osis_common.utils.models import get_object_or_none
from program_management.ddd.repositories import load_tree, persist_tree
from program_management.ddd.service import order_link_service
from program_management.models.enums import node_type
from program_management.models.enums.node_type import NodeType


@login_required
@waffle_flag("education_group_update")
@require_http_methods(['POST'])
def up(request, root_id, link_id):
    return _order_content(request, root_id, link_id, order_link_service.up_link)


@login_required
@waffle_flag("education_group_update")
@require_http_methods(['POST'])
def down(request, root_id, link_id):
    return _order_content(request, root_id, link_id, order_link_service.down_link)


def _order_content(
        request: HttpRequest,
        root_id: int,
        link_id: int,
        order_function
):
    # FIXME When perm refactored remove this code so as to use ddd domain objects
    group_element_year = get_object_or_none(GroupElementYear, pk=link_id)
    perms.can_change_education_group(request.user, group_element_year.parent)

    child_node_type = node_type.NodeType.EDUCATION_GROUP if isinstance(group_element_year.child, EducationGroupYear) \
        else node_type.NodeType.LEARNING_UNIT
    order_function(root_id, group_element_year.parent.id, group_element_year.child.id, child_node_type)

    success_msg = _("The %(acronym)s has been moved") % {'acronym': group_element_year.child.acronym}
    display_success_messages(request, success_msg)

    http_referer = request.META.get('HTTP_REFERER')
    return redirect(http_referer)


@require_http_methods(['POST'])
def copy_to_cache(request):
    element_id = request.POST['element_id']
    element_type = request.POST['element_type']

    element = _get_concerned_object(element_id, element_type)

    return _cache_object(
        request.user,
        None,
        object_to_cache=element,
        action=ElementCache.ElementCacheAction.COPY
    )


@require_http_methods(['POST'])
def cut_to_cache(request):
    group_element_year_id = request.POST['group_element_year_id']
    element_id = request.POST['element_id']
    element_type = request.POST['element_type']

    group_element_year = get_object_or_none(GroupElementYear, pk=group_element_year_id)
    element = _get_concerned_object(element_id, element_type)

    return _cache_object(
        request.user,
        group_element_year,
        object_to_cache=element,
        action=ElementCache.ElementCacheAction.CUT
    )


def _get_concerned_object(element_id: int, element_type: str):
    if element_type == NodeType.LEARNING_UNIT.name:
        object_class = LearningUnitYear
    else:
        object_class = EducationGroupYear

    return get_object_or_404(object_class, pk=element_id)


def _cache_object(
        user: User,
        group_element_year: GroupElementYear,
        object_to_cache,
        action: ElementCache.ElementCacheAction
):
    group_element_year_pk = group_element_year.pk if group_element_year else None
    ElementCache(user).save_element_selected(object_to_cache, source_link_id=group_element_year_pk, action=action.value)
    success_msg = get_clipboard_content_display(object_to_cache, action.value)
    return build_success_json_response(success_msg)
