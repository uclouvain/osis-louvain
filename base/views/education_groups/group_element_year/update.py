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
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import DeleteView
from django.views.generic import UpdateView
from waffle.decorators import waffle_flag

from base.business import group_element_years
from base.business.group_element_years.management import SELECT_CACHE_KEY, select_education_group_year, \
    select_learning_unit_year
from base.business.learning_units.prerequisite import luy_has_or_is_prerequisite
from base.forms.education_group.group_element_year import UpdateGroupElementYearForm
from base.models.education_group_year import EducationGroupYear
from base.models.exceptions import IncompatiblesTypesException
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.utils.utils import get_object_or_none
from base.views.common import display_success_messages, display_warning_messages
from base.views.education_groups import perms
from base.views.education_groups.select import build_success_message, build_success_json_response
from base.views.mixins import AjaxTemplateMixin, FlagMixin, RulesRequiredMixin


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
        "detach",
        "up",
        "down",
    ]
    actions_needing_perm_on_education_group_year_itself = [
        "attach",
    ]

    if _get_data_from_request(request, 'action') in actions_needing_perm_on_parent:
        # In this case, element can be EducationGroupYear OR LearningUnitYear because we check perm on its parent
        perms.can_change_education_group(request.user, group_element_year.parent)
    elif _get_data_from_request(request, 'action') in actions_needing_perm_on_education_group_year_itself:
        # In this case, element MUST BE an EducationGroupYear (we cannot take action on a learning_unit_year)
        if type(element) != EducationGroupYear:
            raise ValidationError(
                "It is forbidden to update the content of an object which is not an EducationGroupYear"
            )
        perms.can_change_education_group(request.user, element)


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


@require_http_methods(['GET', 'POST'])
def _detach(request, group_element_year, *args, **kwargs):
    return DetachGroupElementYearView.as_view()(
        request,
        group_element_year_id=group_element_year.pk,
        *args,
        **kwargs
    )


@require_http_methods(['GET', 'POST'])
def _attach(request, group_element_year, *args, **kwargs):
    parent = kwargs['element']
    try:
        group_element_years.management.attach_from_cache(parent)
        success_msg = _("Attached to \"%(acronym)s\"") % {'acronym': parent}
        display_success_messages(request, success_msg)
    except ObjectDoesNotExist:
        warning_msg = _("Please Select or Move an item before Attach it")
        display_warning_messages(request, warning_msg)
    except IncompatiblesTypesException as e:
        warning_msg = e.errors
        display_warning_messages(request, warning_msg)
    except IntegrityError as e:
        warning_msg = _(str(e))
        display_warning_messages(request, warning_msg)


@require_http_methods(['POST'])
def _select(request, group_element_year, *args, **kwargs):
    element = kwargs['element']
    if type(element) == LearningUnitYear:
        select_learning_unit_year(element)
    elif type(element) == EducationGroupYear:
        select_education_group_year(element)

    success_msg = build_success_message(element)
    return build_success_json_response(success_msg)


def _get_action_method(request):
    available_actions = {
        'up': _up,
        'down': _down,
        'detach': _detach,
        'attach': _attach,
        'select': _select,
    }
    data = getattr(request, request.method, {})
    action = data.get('action')
    if action not in available_actions.keys():
        raise AttributeError('Action should be {}'.format(','.join(available_actions.keys())))
    return available_actions[action]


@method_decorator(login_required, name='dispatch')
class GenericUpdateGroupElementYearMixin(FlagMixin, RulesRequiredMixin, SuccessMessageMixin, AjaxTemplateMixin):
    model = GroupElementYear
    context_object_name = "group_element_year"
    pk_url_kwarg = "group_element_year_id"

    # FlagMixin
    flag = "education_group_update"

    # RulesRequiredMixin
    raise_exception = True
    rules = [perms.can_change_education_group]

    def _call_rule(self, rule):
        """ The permission is computed from the education_group_year """
        return rule(self.request.user, self.education_group_year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['root'] = self.kwargs["root_id"]
        return context

    @property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("education_group_year_id"))

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))


class UpdateGroupElementYearView(GenericUpdateGroupElementYearMixin, UpdateView):
    # UpdateView
    form_class = UpdateGroupElementYearForm
    template_name = "education_group/group_element_year_comment.html"

    # SuccessMessageMixin
    def get_success_message(self, cleaned_data):
        return _("The comments of %(acronym)s has been updated") % {'acronym': self.object.child}

    def get_success_url(self):
        return reverse("education_group_content", args=[self.kwargs["root_id"], self.education_group_year.pk])


class DetachGroupElementYearView(GenericUpdateGroupElementYearMixin, DeleteView):
    # DeleteView
    template_name = "education_group/group_element_year/confirm_detach.html"

    def delete(self, request, *args, **kwargs):
        child_leaf = self.get_object().child_leaf
        if child_leaf and luy_has_or_is_prerequisite(child_leaf):
            raise PermissionDenied

        success_msg = _("\"%(child)s\" has been detached from \"%(parent)s\"") % {
            'child': self.get_object().child,
            'parent': self.get_object().parent,
        }
        display_success_messages(request, success_msg)
        return super().delete(request, *args, **kwargs)

    def _call_rule(self, rule):
        """ The permission is computed from the parent education_group_year """
        return rule(self.request.user, self.get_object().parent)

    def get_success_url(self):
        return self.kwargs.get('http_referer')
