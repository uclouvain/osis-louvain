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
from django import template
from django.contrib import messages
from django.utils.safestring import mark_safe
from base.views.common import MSG_SPECIAL_WARNING_LEVEL, MSG_SPECIAL_WARNING_TITLE_LEVEL

register = template.Library()


@register.simple_tag(takes_context=True)
def as_messages_info(context):
    request = context['request']
    msgs = messages.get_messages(request)

    for m in msgs:
        if 'info' in m.tags:
            return True
    return False


@register.simple_tag(takes_context=True)
def as_messages_warning(context):
    request = context['request']
    msgs = messages.get_messages(request)

    for m in msgs:
        if 'warning' in m.tags:
            return True
    return False


@register.simple_tag(takes_context=True)
def as_messages_error(context):
    request = context['request']
    msgs = messages.get_messages(request)

    for m in msgs:
        if 'error' in m.tags:
            return True
    return False


@register.simple_tag(takes_context=True)
def as_messages_success(context):
    request = context['request']
    msgs = messages.get_messages(request)

    for m in msgs:
        if 'success' in m.tags:
            return True
    return False


@register.simple_tag(takes_context=True)
def as_messages_special_warning(context):
    request = context['request']
    all_messages = messages.get_messages(request)

    messages_update_warning = [m.message for m in all_messages if m.tags == '' and m.level == MSG_SPECIAL_WARNING_LEVEL]
    messages_update_warning_title = None
    for m in all_messages:
        if m.level == MSG_SPECIAL_WARNING_TITLE_LEVEL:
            messages_update_warning_title = m.message
            break
    html = ''
    if messages_update_warning:
        if messages_update_warning_title:
            html = "<b>{}</b><ul>".format(messages_update_warning_title)
        for message in messages_update_warning:
            html += "<li>{}</li>".format(message)
        html += "</ul>"
        return mark_safe(html)
    return None
