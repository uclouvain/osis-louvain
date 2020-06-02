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
import waffle
from django import template
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.translation import gettext as _

from base.business.education_group import can_user_edit_administrative_data
from base.models import program_manager
from base.models.utils.utils import get_verbose_field_value
from base.templatetags.common import ICONS
from osis_role.errors import get_permission_error

register = template.Library()


# TODO: Remove when migration of Program Manager is done with OSIS-Role Module
@register.simple_tag
def have_only_access_to_certificate_aims(user, education_group_year):
    """
    [Backward-compatibility] This templatetag as been created in order to allow
    program_manager to be redirected to update_certificate_aims
    """
    return program_manager.is_program_manager(user, education_group=education_group_year.education_group) \
        and not any((user.is_superuser, user.person.is_faculty_manager, user.person.is_central_manager))


def li_with_permission(context, permission, url, message, url_id, load_modal=False):
    permission_denied_message, disabled, root = _get_permission(context, permission)

    if not disabled:
        href = url
    else:
        href = "#"
        load_modal = False
    return {
        "class_li": disabled,
        "load_modal": load_modal,
        "url": href,
        "id_li": url_id,
        "title": permission_denied_message,
        "text": message,
    }


# TODO : discard callable permission logic
def _get_permission(context, permission):
    permission_denied_message = ""

    education_group_year = context.get('education_group_year')
    person = context.get('person')
    root = context.get("root") or context.get("parent")

    if callable(permission):
        permission_denied_message, result = _get_callable_permission(person, permission, education_group_year)
    else:
        result = person.user.has_perm(permission, obj=education_group_year)
        if not result:
            permission_denied_message = get_permission_error(person.user, permission)

    return permission_denied_message, "" if result else "disabled", root


def _get_callable_permission(person, permission, education_group_year):
    permission_denied_message = ""
    try:
        result = permission(person, education_group_year, raise_exception=True)
    except PermissionDenied as e:
        result = False
        permission_denied_message = str(e)
    return permission_denied_message, result


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def button_edit_administrative_data(context):
    education_group_year = context.get('education_group_year')

    permission_denied_message, is_disabled, root = _get_permission(context, can_user_edit_administrative_data)
    if not permission_denied_message and is_disabled:
        permission_denied_message = _("Only program managers of the education group OR "
                                      "central manager linked to entity can edit.")

    return {
        'class_li': is_disabled,
        'title': permission_denied_message,
        'text': _('Modify'),
        'url': '#' if is_disabled else
        reverse('education_group_edit_administrative', args=[root.pk, education_group_year.pk])
    }


@register.inclusion_tag("blocks/button/button_order.html", takes_context=True)
def button_order_with_permission(context, title, id_button, value):
    permission_denied_message, disabled, root = _get_permission(context, 'base.change_link_data')

    if disabled:
        title = permission_denied_message
    else:
        education_group_year = context.get('education_group_year')
        person = context.get('person')

    if value == "up" and context["forloop"]["first"]:
        disabled = "disabled"

    if value == "down" and context["forloop"]["last"]:
        disabled = "disabled"

    return {
        'title': title,
        'id': id_button,
        'value': value,
        'disabled': disabled,
        'icon': ICONS[value],
    }


@register.simple_tag(takes_context=True)
def url_resolver_match(context):
    return context.request.resolver_match.url_name


@register.inclusion_tag('blocks/button/li_template.html')
def link_pdf_content_education_group(url):
    action = _("Generate pdf")
    if waffle.switch_is_active('education_group_year_generate_pdf'):
        disabled = ''
        title = action
        load_modal = True
    else:
        disabled = 'disabled'
        title = _('Generate PDF not available. Please use EPC.')
        load_modal = False
        url = '#'

    return {
        "class_li": disabled,
        "load_modal": load_modal,
        "url": url,
        "id_li": "btn_operation_pdf_content",
        "title": title,
        "text": action,
    }


@register.inclusion_tag("blocks/dl/dl_with_parent.html", takes_context=True)
def dl_with_parent(context, key, dl_title="", class_dl="", default_value=None, html_id=None):
    """
    Tag to render <dl> for details of education_group.
    If the fetched value does not exist for the current education_group_year,
    the method will try to fetch the parent's value and display it in another style
    (strong, blue).
    """
    obj = context["education_group_year"]
    parent = context["parent"]

    return dl_with_parent_without_context(key, obj, parent, dl_title=dl_title, class_dl=class_dl,
                                          default_value=default_value, html_id=html_id)


@register.inclusion_tag("blocks/dl/dl_with_parent.html", takes_context=False)
def dl_with_parent_without_context(key, obj, parent, dl_title="", class_dl="", default_value=None, html_id=None):
    value = None
    parent_value = None
    if obj:
        value = get_verbose_field_value(obj, key)

        if not dl_title:
            dl_title = obj._meta.get_field(key).verbose_name

        if value is None or value == "":
            parent_value = get_verbose_field_value(parent, key)
        else:
            parent, parent_value = None, None

    return {
        'label': _(dl_title),
        'value': _bool_to_string(value),
        'parent_value': _bool_to_string(parent_value),
        'class_dl': class_dl,
        'default_value': default_value,
        'html_id': html_id,
    }


def _bool_to_string(value):
    if value is None:
        return value

    # In this case, None has a different value meaning than usual (maybe)
    if isinstance(value, bool):
        return "yes" if value else "no"

    return str(value)
