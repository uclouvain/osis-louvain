#############################################################################
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
from django import template
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from base.business.learning_units.perms import is_eligible_for_modification, is_eligible_for_modification_end_date, \
    is_eligible_to_edit_proposal, is_eligible_for_cancel_of_proposal, \
    is_eligible_to_consolidate_proposal, is_eligible_to_delete_learning_unit_year, \
    is_eligible_to_modify_end_year_by_proposal, is_eligible_to_modify_by_proposal
from base.business.learning_units.perms import is_year_editable
from base.models.person import find_by_user

register = template.Library()

MSG_IS_NOT_A_PROPOSAL = _("Isn't a proposal")
MSG_PROPOSAL_NOT_ON_CURRENT_LU = _("Proposal isn't on current learning unit year")
DISABLED = "disabled"


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_edit_lu(context, url, message, url_id="link_edit_lu"):
    data = _get_common_data(context, message, url, url_id)
    data['permission'] = is_eligible_for_modification
    return li_with_permission(data)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_edit_date_lu(context, url, message, url_id="link_edit_date_lu"):
    data = _get_common_data(context, message, url, url_id)
    data['permission'] = is_eligible_for_modification_end_date
    return li_with_permission(data)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_suppression_proposal(context, url, message, url_id="link_proposal_suppression", js_script=''):
    data = _get_common_proposal_data(context, message, url, url_id)
    data['permission'] = is_eligible_to_modify_end_year_by_proposal
    data['obj'] = context['learning_unit_year']
    data['load_modal'] = False

    return li_with_permission(data)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_modification_proposal(context, url, message, url_id="link_proposal_modification", js_script=''):
    data = _get_common_data(context, message, url, url_id)
    data['permission'] = is_eligible_to_modify_by_proposal
    return li_with_permission(data)


@register.inclusion_tag('blocks/button/li_template.html', takes_context=True)
def li_edit_proposal(context, url, message, url_id="link_proposal_edit", js_script=''):
    data = _get_common_proposal_data(context, message, url, url_id)
    data['permission_function'] = is_eligible_to_edit_proposal
    data['obj'] = context['proposal']
    return li_with_permission_for_proposal(data)


@register.inclusion_tag('blocks/button/li_template_lu.html', takes_context=True)
def li_cancel_proposal(context, url, message, data_target, url_id="link_cancel_proposal", js_script=''):
    data = _get_common_proposal_data(context, message, url, url_id)
    data['permission_function'] = is_eligible_for_cancel_of_proposal
    data['obj'] = context['proposal']
    data['js_script'] = js_script
    data['load_modal'] = True
    data['data_target'] = data_target
    return li_with_permission_for_proposal(data)


def _get_common_proposal_data(context, message, url, url_id):
    data = {'context': context,
            'url': url,
            'message': message,
            'url_id': url_id,
            'load_modal': False,
            'js_script': '',
            'data_target': '',
            }
    return data


@register.inclusion_tag('blocks/button/li_template_lu.html', takes_context=True)
def li_consolidate_proposal(context, url, message, data_target, url_id="link_consolidate_proposal", js_script=''):
    data = _get_common_proposal_data(context, message, url, url_id)
    data['permission_function'] = is_eligible_to_consolidate_proposal
    data['obj'] = context['proposal']
    data['js_script'] = js_script
    data['load_modal'] = True
    data['data_target'] = data_target
    return li_with_permission_for_proposal(data)


@register.inclusion_tag('blocks/button/li_template_lu.html', takes_context=True)
def li_delete_all_lu(context, url, message, data_target, url_id="link_delete_lus"):
    data = _get_common_data(context, message, url, url_id)
    data['permission'] = is_eligible_to_delete_learning_unit_year
    data['load_modal'] = True
    data['data_target'] = data_target
    return li_with_permission(data)


def _get_common_data(context, message, url, url_id):
    return {'context': context, 'url': url, 'message': message,
            'url_id': url_id, 'load_modal': False,
            'data_target': ''}


def li_with_permission(data):
    context = data['context']
    permission = data['permission']
    url = data['url']
    message = data['message']
    url_id = data['url_id']
    load_modal = data.get('load_modal', False)
    data_target = data.get('data_target', '')

    permission_denied_message, disabled = _get_permission(context, permission)

    if not disabled:
        href = url
    else:
        href = "#"
        load_modal = False
        data_target = ''

    return {
        "class_li": disabled,
        "load_modal": load_modal,
        "url": href,
        "id_li": url_id,
        "title": permission_denied_message,
        "text": message,
        "data_target": data_target
    }


def _get_permission(context, permission):
    return _get_permission_result(context.get('learning_unit_year'),
                                  permission,
                                  find_by_user(context.get('user')))


def _get_permission_result(learning_unit_year, permission, person):
    permission_denied_message = ""
    try:
        result = permission(learning_unit_year, person, raise_exception=True)
    except PermissionDenied as e:
        result = False
        permission_denied_message = str(e)

    return permission_denied_message, "" if result else DISABLED


# TODO data should be a kwargs
def li_with_permission_for_proposal(data):
    context = data['context']
    permission = data['permission_function']
    url = data['url']
    message = data['message']
    url_id = data['url_id']
    load_modal = data.get('load_modal', False)
    data_target = data.get('data_target', '')
    js_script = data.get('js_script', '')
    obj = data['obj']

    proposal = context['proposal']

    permission_denied_message, disabled = is_valid_proposal(context)

    if not disabled:
        if not is_year_editable(proposal.learning_unit_year, raise_exception=False):
            disabled = "disabled"
            permission_denied_message = "{}.  {}".format(
                _("You can't modify learning unit under year : %(year)d") %
                {"year": settings.YEAR_LIMIT_LUE_MODIFICATION + 1},
                _("Modifications should be made in EPC for year %(year)d") %
                {"year": proposal.learning_unit_year.academic_year.year},
                )
        else:
            permission_denied_message, disabled = _get_permission_proposal(context, permission, obj)

    if not disabled:
        href = url
    else:
        href = "#"
        load_modal = False
        data_target = ''

    return {
        "class_li": disabled,
        "load_modal": load_modal,
        "url": href,
        "id_li": url_id,
        "title": permission_denied_message,
        "text": message,
        "js_script": js_script,
        "data_target": data_target
    }


def _get_permission_proposal(context, permission, object):
    # object is sometimes a proposal, sometimes a learning_unit_year it's why it's call 'object'
    return _get_permission_result(object,
                                  permission,
                                  find_by_user(context.get('user')))


def is_valid_proposal(context):
    current_learning_unit_year = context.get('learning_unit_year')
    proposal = context.get('proposal')
    if not proposal:
        return _(MSG_IS_NOT_A_PROPOSAL), "disabled"
    else:

        if proposal.learning_unit_year != current_learning_unit_year:
            return _(MSG_PROPOSAL_NOT_ON_CURRENT_LU), "disabled"
    return "", ""
