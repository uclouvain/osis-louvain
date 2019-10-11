##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _, gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView
from waffle.decorators import waffle_flag

from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.utils.utils import get_object_or_none
from base.utils.cache import ElementCache
from base.views.common import display_success_messages, display_warning_messages, display_error_messages
from base.views.education_groups import perms
from base.views.education_groups.detail import EducationGroupGenericDetailView
from base.views.education_groups.perms import can_change_education_group
from base.views.education_groups.select import build_success_message, build_success_json_response
from base.views.mixins import RulesRequiredMixin, AjaxTemplateMixin
from program_management.business.group_element_years.postponement import PostponeContent, NotPostponeError
from program_management.forms.group_element_year import GroupElementYearForm
from program_management.views.group_element_year import perms as group_element_year_perms
from program_management.views.group_element_year.common import GenericGroupElementYearMixin


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
def _select(request, group_element_year, *args, **kwargs):
    element = kwargs['element']
    group_element_year_pk = group_element_year.pk if group_element_year else None
    ElementCache(request.user).save_element_selected(element, source_link_id=group_element_year_pk)
    success_msg = build_success_message(element)
    return build_success_json_response(success_msg)


def _get_action_method(request):
    available_actions = {
        'up': _up,
        'down': _down,
        'select': _select,
    }
    data = getattr(request, request.method, {})
    action = data.get('action')
    if action not in available_actions.keys():
        raise AttributeError('Action should be {}'.format(','.join(available_actions.keys())))
    return available_actions[action]


class UpdateGroupElementYearView(GenericGroupElementYearMixin, UpdateView):
    # UpdateView
    form_class = GroupElementYearForm
    template_name = "group_element_year/group_element_year_comment_inner.html"

    rules = [group_element_year_perms.can_update_group_element_year]

    def _call_rule(self, rule):
        return rule(self.request.user, self.get_object())

    # SuccessMessageMixin
    def get_success_message(self, cleaned_data):
        return _("The link of %(acronym)s has been updated") % {'acronym': self.object.child}

    def get_success_url(self):
        # We can just reload the page
        return


class PostponeGroupElementYearView(RulesRequiredMixin, AjaxTemplateMixin, EducationGroupGenericDetailView):
    template_name = "group_element_year/confirm_postpone_content_inner.html"

    # FlagMixin
    flag = "education_group_update"

    # RulesRequiredMixin
    rules = [can_change_education_group]

    with_tree = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warning_message"] = _("Are you sure you want to postpone the content in %(root)s?") % {
            "root": self.root
        }
        return context

    def post(self, request, **kwargs):
        try:
            postponer = PostponeContent(self.root.previous_year())
            postponer.postpone()
            success = _("%(count_elements)s OF(s) and %(count_links)s link(s) have been postponed with success.") % {
                'count_elements': postponer.number_elements_created,
                'count_links': postponer.number_links_created
            }
            display_success_messages(request, success)
            display_warning_messages(request, postponer.warnings)

        except NotPostponeError as e:
            display_error_messages(request, str(e))

        return JsonResponse({
            'success_url': reverse(
                "education_group_read",
                args=[
                    kwargs["root_id"],
                    kwargs["education_group_year_id"]
                ]
            )})
