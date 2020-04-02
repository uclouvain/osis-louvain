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
from django.contrib.auth.decorators import login_required
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


@login_required
@waffle_flag("education_group_update")
def management(request):
    root_id = _get_data_from_request(request, 'root_id')
    group_element_year_id = _get_data_from_request(request, 'group_element_year_id') or 0
    group_element_year = get_object_or_none(GroupElementYear, pk=group_element_year_id)
    element_id = _get_data_from_request(request, 'element_id')
    element = _get_concerned_object(element_id, group_element_year)

    _check_perm_for_management(request, element, group_element_year)

    action_method = _get_action_method(request)
    source = _get_data_from_request(request, 'source')
    http_referer = request.META.get('HTTP_REFERER')

    response = action_method(
        request,
        group_element_year,
        root_id=root_id,
        element=element,
        source=source,
        http_referer=http_referer,
    )
    if response:
        return response

    return redirect(http_referer)


def _get_data_from_request(request, name):
    return getattr(request, request.method, {}).get(name)


def _get_concerned_object(element_id, group_element_year):
    if group_element_year and group_element_year.child_leaf:
        object_class = LearningUnitYear
    else:
        object_class = EducationGroupYear

    return get_object_or_404(object_class, pk=element_id)


def _check_perm_for_management(request, element, group_element_year):
    actions_needing_perm_on_parent = [
        "up",
        "down",
    ]

    if _get_data_from_request(request, 'action') in actions_needing_perm_on_parent:
        # In this case, element can be EducationGroupYear OR LearningUnitYear because we check perm on its parent
        perms.can_change_education_group(request.user, group_element_year.parent)


@require_http_methods(['POST'])
def _up(request, group_element_year, *args, **kwargs):
    success_msg = _("The %(acronym)s has been moved") % {'acronym': group_element_year.child}
    group_element_year.up()
    display_success_messages(request, success_msg)


@require_http_methods(['POST'])
def _down(request, group_element_year, *args, **kwargs):
    success_msg = _("The %(acronym)s has been moved") % {'acronym': group_element_year.child}
    group_element_year.down()
    display_success_messages(request, success_msg)


@require_http_methods(['POST'])
def _copy_to_cache(request, group_element_year, *args, **kwargs):
    return _cache_object(
        request.user,
        group_element_year,
        object_to_cache=kwargs['element'],
        action=ElementCache.ElementCacheAction.COPY.value
    )


@require_http_methods(['POST'])
def _cut_to_cache(request, group_element_year, *args, **kwargs):
    action = ElementCache.ElementCacheAction.CUT.value
    if not group_element_year:
        action = ElementCache.ElementCacheAction.COPY.value
    return _cache_object(
        request.user,
        group_element_year,
        object_to_cache=kwargs['element'],
        action=action
    )


def _cache_object(user, group_element_year, object_to_cache, action):
    group_element_year_pk = group_element_year.pk if group_element_year else None
    ElementCache(user).save_element_selected(object_to_cache, source_link_id=group_element_year_pk, action=action)
    success_msg = get_clipboard_content_display(object_to_cache, action)
    return build_success_json_response(success_msg)


def _get_action_method(request):
    available_actions = {
        'up': _up,
        'down': _down,
        'copy': _copy_to_cache,
        'cut': _cut_to_cache,
    }
    data = getattr(request, request.method, {})
    action = data.get('action')
    if action not in available_actions.keys():
        raise AttributeError('Action should be {}'.format(','.join(available_actions.keys())))
    return available_actions[action]
