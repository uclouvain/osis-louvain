##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator

from django import template
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from backoffice.settings import base
from base.business.education_group import can_user_edit_administrative_data
from base.business.education_groups.perms import is_eligible_to_delete_education_group, \
    is_eligible_to_change_education_group, is_eligible_to_add_training, \
    is_eligible_to_add_mini_training, is_eligible_to_add_group, is_eligible_to_change_achievement, \
    is_eligible_to_delete_achievement, is_eligible_to_postpone_education_group
from base.models.academic_year import AcademicYear
from base.models.enums.learning_unit_year_periodicity import BIENNIAL_EVEN, BIENNIAL_ODD, ANNUAL

OPTIONAL_PNG = base.STATIC_URL + 'img/education_group_year/optional.png'
MANDATORY_PNG = base.STATIC_URL + 'img/education_group_year/mandatory.png'
VALIDATE_CASE_JPG = base.STATIC_URL + 'img/education_group_year/validate_case.jpg'
INVALIDATE_CASE_JPG = base.STATIC_URL + 'img/education_group_year/invalidate_case.png'
DELTA = base.STATIC_URL + 'img/education_group_year/delta.png'
BISANNUAL_EVEN = base.STATIC_URL + 'img/education_group_year/bisannual_even.png'
BISANNUAL_ODD = base.STATIC_URL + 'img/education_group_year/bisannual_odd.png'

CHILD_BRANCH = """\
<tr>
    <td style="padding-left:{padding}em;">
        {constraint}
        <div style="word-break: keep-all;">
            <img src="{icon_list_2}" height="10" width="10">
            {value}
            {remark}
            {comment}
            {sublist}
        </div>
    </td>
</tr>
"""

CHILD_LEAF = """\
<tr>
    <td style="padding-left:{padding}em;">
        <div style="word-break: keep-all;">
            <img src="{icon_list_1}" height="14" width="17">
            <img src="{icon_list_2}" height="10" width="10">
            {value}
            <img src="{icon_list_3}" height="10" width="10">
            <img src="{icon_list_4}" height="10" width="10">
            {comment}
            {sublist}
        </div>
    </td>
    <td style="text-align: center;">{an_1}</td>
    <td style="text-align: center;">{an_2}</td>
    <td style="text-align: center;">{an_3}</td>
</tr>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
BRANCH_REMARK = """\
        <div style="word-break: keep-all;margin-left: 14px;">
            {remark_value}
        </div>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
CHILD_COMMENT = """\
        <div style="word-break: keep-all;margin-left: 32px;">
            ({comment_value})
        </div>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
BRANCH_CONSTRAINT = """\
        <div style="font-style: italic;">
            {constraint_value}
        </div>
"""

# TODO Use inclusion tags instead
BUTTON_ORDER_TEMPLATE = """
<button type="submit" title="{}" class="btn btn-default btn-sm" 
    id="{}" data-toggle="tooltip-wrapper" name="action" value="{}" {}>
    <i class="fa {}"></i>
</button>
"""

ICONS = {
    "up": "fa-arrow-up",
    "down": "fa-arrow-down",
    "detach": "fa-close",
    "edit": "fa-edit",
}

register = template.Library()


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_deletion_perm(context, url, message, url_id="link_delete"):
    return li_with_permission(context, is_eligible_to_delete_education_group, url, message, url_id, True)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_update_perm(context, url, message, url_id="link_update"):
    return li_with_permission(context, is_eligible_to_change_education_group, url, message, url_id)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_create_perm_training(context, url, message, url_id="link_create_training"):
    return li_with_permission(context, is_eligible_to_add_training, url, message, url_id, True)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_create_perm_mini_training(context, url, message, url_id="link_create_mini_training"):
    return li_with_permission(context, is_eligible_to_add_mini_training, url, message, url_id, True)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_create_perm_group(context, url, message, url_id="link_create_group"):
    return li_with_permission(context, is_eligible_to_add_group, url, message, url_id, True)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_with_postpone_perm_training(context, url_id="link_postpone_training"):
    root = context['root']
    education_group_year = context['education_group_year']
    url = reverse('postpone_education_group', args=[root.pk, education_group_year.pk])

    try:
        last_academic_year = education_group_year.academic_year.past()
    except AcademicYear.DoesNotExist:
        last_academic_year = "last year"

    message = _('Copy the content from %(previous_anac)s to %(current_anac)s') % {
        'previous_anac':  str(last_academic_year),
        'current_anac':  str(education_group_year.academic_year)

    }
    return li_with_permission(context, is_eligible_to_postpone_education_group, url, message, url_id, True)


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


def _get_permission(context, permission):
    permission_denied_message = ""

    education_group_year = context.get('education_group_year')
    person = context.get('person')
    root = context.get("root") or context.get("parent")

    try:
        result = permission(person, education_group_year, raise_exception=True)

    except PermissionDenied as e:
        result = False
        permission_denied_message = str(e)

    return permission_denied_message, "" if result else "disabled", root


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def button_edit_administrative_data(context):
    education_group_year = context.get('education_group_year')

    permission_denied_message, is_disabled, root = _get_permission(context, can_user_edit_administrative_data)
    if not permission_denied_message:
        permission_denied_message = _("Only program managers of the education group OR "
                                      "central manager linked to entity can edit.")

    return {
        'is_disabled': is_disabled,
        'message': permission_denied_message,
        'text': _('Edit'),
        'url': reverse('education_group_edit_administrative', args=[root.pk, education_group_year.pk])
    }


@register.simple_tag(takes_context=True)
def button_order_with_permission(context, title, id_button, value):
    permission_denied_message, disabled, root = _get_permission(context, is_eligible_to_change_education_group)

    if disabled:
        title = permission_denied_message

    if value == "up" and context["forloop"]["first"]:
        disabled = "disabled"

    if value == "down" and context["forloop"]["last"]:
        disabled = "disabled"

    return mark_safe(BUTTON_ORDER_TEMPLATE.format(title, id_button, value, disabled, ICONS[value]))


@register.inclusion_tag("blocks/button/button_template.html", takes_context=True)
def button_with_permission(context, title, value, url):
    permission_denied_message, disabled, root = _get_permission(context, is_eligible_to_change_education_group)

    if disabled:
        title = permission_denied_message

    return {
        'load_modal': True,
        'title': title,
        'class_button': "btn-default btn-sm " + disabled,
        'icon': ICONS[value],
        'url': url,
    }


@register.filter(is_safe=True, needs_autoescape=True)
def pdf_tree_list(value, autoescape=True):
    if autoescape:
        escaper = conditional_escape
    else:
        def escaper(x):
            return x
    return mark_safe(list_formatter(value))


def walk_items(item_list):
    if item_list:
        item_iterator = iter(item_list)
        try:
            item = next(item_iterator)
            while True:
                try:
                    next_item = next(item_iterator)
                except StopIteration:
                    yield item, None
                    break
                if not isinstance(next_item, six.string_types):
                    try:
                        iter(next_item)
                    except TypeError:
                        pass
                    else:
                        yield item, next_item
                        item = next(item_iterator)
                        continue
                yield item, None
                item = next_item
        except StopIteration:
            pass
    else:
        return ""


def list_formatter(item_list, tabs=1, depth=None):
    output = []
    depth = depth if depth else 1
    for item, children in walk_items(item_list):
        sublist = ''
        padding = 2 * depth
        if children:
            sublist = '%s' % (
                list_formatter(children, tabs + 1, depth + 1))
        append_output(item, output, padding, sublist)
    return '\n'.join(output)


def append_output(item, output, padding, sublist):
    comment = CHILD_COMMENT.format(
        comment_value=item.verbose_comment
    ) if item.verbose_comment else ""

    if item.child_leaf:
        mandatory_picture = get_mandatory_picture(item)
        output.append(
            CHILD_LEAF.format(padding=padding,
                              icon_list_1=get_case_picture(item),
                              icon_list_2=mandatory_picture,
                              icon_list_3=get_status_picture(item),
                              icon_list_4=get_biennial_picture(item),
                              value=force_text(item.verbose),
                              comment=comment,
                              sublist=sublist,
                              an_1=check_block(item, "1"),
                              an_2=check_block(item, "2"),
                              an_3=check_block(item, "3")
                              )
        )
    else:
        constraint = BRANCH_CONSTRAINT.format(
            constraint_value=item.child_branch.verbose_constraint
        ) if item.child_branch.constraint_type else ""

        remark = BRANCH_REMARK.format(remark_value=item.child.verbose_remark) if item.child.verbose_remark else ""

        output.append(
            CHILD_BRANCH.format(padding=padding,
                                constraint=constraint,
                                icon_list_2=get_mandatory_picture(item),
                                value=force_text(item.verbose),
                                remark=remark,
                                comment=comment,
                                sublist=sublist
                                )
        )


def get_status_picture(item):
    return DELTA if not item.child_leaf.status else ""


def get_biennial_picture(item):
    if item.child_leaf.periodicity == BIENNIAL_EVEN:
        return BISANNUAL_EVEN
    elif item.child_leaf.periodicity == BIENNIAL_ODD:
        return BISANNUAL_ODD
    else:
        return ""


def get_mandatory_picture(item):
    return MANDATORY_PNG if item.is_mandatory else OPTIONAL_PNG


def get_case_picture(item):
    if item.child_leaf.status:
        if item.child_leaf.periodicity == ANNUAL:
            return VALIDATE_CASE_JPG
        elif item.child_leaf.periodicity == BIENNIAL_EVEN and item.child_leaf.academic_year.is_even:
            return VALIDATE_CASE_JPG
        elif item.child_leaf.periodicity == BIENNIAL_ODD and item.child_leaf.academic_year.is_odd:
            return VALIDATE_CASE_JPG
    return INVALIDATE_CASE_JPG


def check_block(item, value):
    return "X" if item.block and value in item.block else ""


@register.simple_tag(takes_context=True)
def url_resolver_match(context):
    return context.request.resolver_match.url_name


@register.simple_tag(takes_context=True)
def link_detach_education_group(context, url):
    onclick = """onclick="select()" """
    action = "Detach"
    if context['can_change_education_group'] and context['group_to_parent'] != '0':
        li_attributes = """ id="btn_operation_detach_{group_to_parent}" class="trigger_modal" data-url={url} """.format(
            group_to_parent=context['group_to_parent'],
            url=url,
        )
        a_attributes = """ href="#" title="{title}" {onclick} """.format(title=_(action), onclick=onclick)
    else:
        li_attributes = """ class="disabled" """
        title = ""
        if not context['can_change_education_group']:
            title += _("The user has not permission to change education groups.")
        if context['group_to_parent'] == '0':
            title += " " + _("It is not possible to %(action)s the root element.") % {
                "action": str.lower(_(action))
            }

        a_attributes = """ title="{title}" """.format(title=title)
    text = _(action)
    html_template = """
        <li {li_attributes}>
            <a {a_attributes} data-toggle="tooltip">{text}</a>
        </li>
    """

    return mark_safe(
        html_template.format(
            li_attributes=li_attributes,
            a_attributes=a_attributes,
            text=text,
        )
    )


@register.inclusion_tag('blocks/button/li_template.html')
def link_pdf_content_education_group(url):
    action = _("Generate pdf")

    return {
        "class_li": "",
        "load_modal": True,
        "url": url,
        "id_li": "btn_operation_pdf_content",
        "title": action,
        "text": action,
    }


@register.inclusion_tag("blocks/dl/dl_with_parent.html", takes_context=True)
def dl_with_parent(context, dl_title, key, class_dl="", default_value=None):
    """
    Tag to render <dl> for details of education_group.
    If the fetched value does not exist for the current education_group_year,
    the method will try to fetch the parent's value and display it in another style
    (strong, blue).

    :param context: context of the page given by django inclusion tag
    :param dl_title: text to display in <dt>
    :param key: attr to fetch value from education_group_year (can be a property)
    :param class_dl: additional html class
    :param default_value: display a default value in <dd> if no value was found.
    :return: dict
    """
    education_group_year = context.get('education_group_year')
    value = _fetch_value_with_attrgetter(education_group_year, key)

    if value is None or value == "":
        parent = context.get("parent")
        parent_value = _fetch_value_with_attrgetter(parent, key)
    else:
        parent, parent_value = None, None

    return {
        'label': _(dl_title),
        'value': _bool_to_string(value),
        'parent_value': _bool_to_string(parent_value),
        'class_dl': class_dl,
        'default_value': default_value,
    }


def _bool_to_string(value):
    if value is None:
        return value

    # In this case, None has a different value meaning than usual (maybe)
    if isinstance(value, bool):
        return "yes" if value else "no"

    return str(value)


def _fetch_value_with_attrgetter(obj, attrs):
    """ Use attrgetter to support attrs with '.' """
    try:
        return obj and operator.attrgetter(attrs)(obj)
    except AttributeError:
        return None


@register.simple_tag(takes_context=True)
def permission_change_achievement(context):
    return _get_permission(context, is_eligible_to_change_achievement)[1]


@register.simple_tag(takes_context=True)
def permission_delete_achievement(context):
    return _get_permission(context, is_eligible_to_delete_achievement)[1]


@register.simple_tag(takes_context=True)
def permission_create_achievement(context):
    return _get_permission(context, is_eligible_to_change_achievement)[1]
