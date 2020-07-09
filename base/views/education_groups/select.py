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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from waffle.decorators import waffle_flag

from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache


@login_required
@waffle_flag("copy_education_group_to_cache")
def copy_education_group_to_cache(request, root_id=None, education_group_year_id=None):
    education_group_year = get_object_or_404(EducationGroupYear, pk=request.POST['element_id'])
    redirect_to = reverse(
        'education_group_read',
        args=[
            root_id,
            education_group_year_id,
        ]
    )
    return _cache_object_and_redirect(request, education_group_year, redirect_to=redirect_to)


@login_required
@waffle_flag("copy_education_group_to_cache")
@require_http_methods(['POST'])
def copy_learning_unit_to_cache(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    redirect_to = reverse(
        'learning_unit',
        args=[learning_unit_year_id]
    )
    return _cache_object_and_redirect(request, learning_unit_year, redirect_to=redirect_to)


def _cache_object_and_redirect(request, object_to_cache, redirect_to):
    ElementCache(request.user).save_element_selected(object_to_cache)
    success_message = get_clipboard_content_display(object_to_cache, ElementCache.ElementCacheAction.COPY.value)
    if request.is_ajax():
        return build_success_json_response(success_message)
    else:
        messages.add_message(request, messages.INFO, success_message)
        return redirect(redirect_to)


def get_clipboard_content_display(obj, action):
    msg_template = "<strong>{clipboard_title}</strong><br>{object_str}"
    return msg_template.format(
        clipboard_title=_get_clipboard_title(action),
        object_str=str(obj),
    )


def _get_clipboard_title(action):
    if action == ElementCache.ElementCacheAction.CUT.value:
        return _("Cut element")
    elif action == ElementCache.ElementCacheAction.COPY.value:
        return _("Copied element")
    else:
        return ""


def build_success_json_response(success_message):
    data = {'success_message': success_message}
    return JsonResponse(data)
