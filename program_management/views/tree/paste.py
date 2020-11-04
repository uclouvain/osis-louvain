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
import functools
import itertools
from typing import List

from django import shortcuts
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import formset_factory
from django.http import JsonResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.base import View

import program_management.ddd.command
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.exceptions import InvalidFormException
from base.utils.cache import ElementCache
from base.views.common import display_warning_messages, display_success_messages, display_error_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.models.group_year import GroupYear
from osis_role import errors
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd.business_types import *
from program_management.ddd.domain import node
from program_management.ddd.repositories import node as node_repository, load_node
from program_management.ddd.service.read import element_selected_service, check_paste_node_service
from program_management.forms.tree.paste import PasteNodeForm, BasePasteNodesFormset


class PasteNodesView(AjaxPermissionRequiredMixin, AjaxTemplateMixin, SuccessMessageMixin, FormView):
    template_name = "tree/link_update_inner.html"
    permission_required = "base.can_attach_node"

    def has_permission(self):
        return self._has_permission_to_detach() & super().has_permission()

    def get_permission_error(self, request) -> str:
        if not self._has_permission_to_detach():
            return errors.get_permission_error(request.user, "base.can_detach_node")
        return super().get_permission_error(request)

    @functools.lru_cache()
    def _has_permission_to_detach(self) -> bool:
        if not self.path_to_detach_from:
            return True
        node_to_detach_from = int(self.path_to_detach_from.split("|")[-2])
        objs_to_detach_from = GroupYear.objects.filter(element__id=node_to_detach_from)
        return all(
            self.request.user.has_perm("base.can_detach_node", obj_to_detach)
            for obj_to_detach in objs_to_detach_from
        )

    def get_permission_object(self) -> GroupYear:
        node_to_paste_to_id = int(self.request.GET['path'].split("|")[-1])
        return shortcuts.get_object_or_404(GroupYear, element__pk=node_to_paste_to_id)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["content_formset"] = context_data.pop("form")

        if not self.nodes_to_paste:
            display_warning_messages(self.request, _("Please cut or copy an item before paste"))

        error_messages = list(itertools.chain.from_iterable(
            check_paste(
                self.request,
                {
                    "element_code": node_to_paste.code,
                    "element_year": node_to_paste.year,
                    "path_to_detach": self.path_to_detach_from
                }
            )
            for node_to_paste in self.nodes_to_paste
        ))
        if error_messages:
            display_error_messages(self.request, error_messages)

        return context_data

    @cached_property
    def nodes_to_paste(self) -> List['Node']:
        year = self.request.GET.get("year")
        codes = self.request.GET.getlist("codes", [])
        if codes and year:
            nodes_to_paste = [{"element_code": code, "element_year": int(year)} for code in codes]
        else:
            element_selected = element_selected_service.retrieve_element_selected(self.request.user.id)
            if not element_selected:
                return []
            nodes_to_paste = [element_selected]
        node_identities = [node.NodeIdentity(ele["element_code"], ele["element_year"]) for ele in nodes_to_paste]
        return node_repository.NodeRepository.search(node_identities)

    @cached_property
    def parent_node(self) -> 'Node':
        node_to_paste_into_id = int(self.request.GET['path'].split("|")[-1])
        return load_node.load(node_to_paste_into_id)

    @property
    def path_to_detach_from(self) -> str:
        codes = self.request.GET.getlist("codes", [])
        if codes:
            return ""

        cached_element_selected = element_selected_service.retrieve_element_selected(self.request.user.id)
        if cached_element_selected:
            return cached_element_selected['path_to_detach']
        return ''

    def get_form_class(self):
        return formset_factory(form=PasteNodeForm, formset=BasePasteNodesFormset, extra=len(self.nodes_to_paste))

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(form_kwargs=self.get_form_kwargs(), data=self.request.POST or None)

    def get_form_kwargs(self) -> List[dict]:
        return [
            {
                'parent_obj': self.parent_node,
                'child_obj': node_to_paste,
                'path_to_detach': self.path_to_detach_from,
                'initial': {
                    "is_mandatory": True,
                    "relative_credits": int(node_to_paste.credits)
                    if node_to_paste.credits is not None else node_to_paste.credits
                }
            }
            for node_to_paste in self.nodes_to_paste
        ]

    def form_valid(self, formset: BasePasteNodesFormset):
        try:
            formset.save()

            messages = self.get_success_messages()
            display_success_messages(self.request, messages)

            ElementCache(self.request.user.id).clear()

            return super().form_valid(formset)
        except InvalidFormException:
            return self.form_invalid(formset)

    def get_success_messages(self) -> List['str']:
        messages = []
        paste_action_message = _("pasted") if ElementCache(self.request.user.id).cached_data else _("added")
        for child_node in self.nodes_to_paste:
            messages.append(
                _("\"%(child)s\" has been %(copy_message)s into \"%(parent)s\"") % {
                    "child": child_node,
                    "copy_message": paste_action_message,
                    "parent": self.parent_node,
                }
            )
        return messages

    def get_success_url(self):
        return


class CheckPasteView(LoginRequiredMixin, View):
    def _retrieve_elements_selected(self) -> List[dict]:
        year = self.request.GET.get("year")
        codes = self.request.GET.getlist("codes", [])
        if codes and year:
            return [{"element_code": code, "element_year": int(year), "path_to_detach": None} for code in codes]
        return []

    def get(self, request, *args, **kwargs):
        elements_to_paste = self._retrieve_elements_selected()
        if not elements_to_paste:
            return JsonResponse({"error_messages": [_("Please cut or copy an item before paste")]})

        error_messages = list(itertools.chain.from_iterable(
            check_paste(request, element) for element in elements_to_paste
        ))
        if error_messages:
            return JsonResponse({"error_messages": error_messages})

        return JsonResponse({"error_messages": []})


def check_paste(request, node_to_paste) -> List[str]:
    root_id = int(request.GET["path"].split("|")[0])
    check_command = program_management.ddd.command.CheckPasteNodeCommand(
        root_id=root_id,
        node_to_past_code=node_to_paste["element_code"],
        node_to_paste_year=node_to_paste["element_year"],
        path_to_detach=node_to_paste["path_to_detach"],
        path_to_paste=request.GET["path"],
    )
    check_key = '{}|{}'.format(request.GET['path'], node_to_paste['element_code'])

    try:
        if not request.session.get(check_key):
            check_paste_node_service.check_paste(check_command)
    except MultipleBusinessExceptions as exceptions:
        return [business_exception.message for business_exception in exceptions.exceptions]

    # cache result to avoid double check
    if request.session.get(check_key):
        del request.session[check_key]
    else:
        request.session[check_key] = True

    return []
