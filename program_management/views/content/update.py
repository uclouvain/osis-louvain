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
import functools
from typing import List, Dict, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.forms.exceptions import InvalidFormException
from base.utils.urls import reverse_with_get
from base.views.common import display_success_messages, display_error_messages, check_formations_impacted_by_update, \
    display_warning_messages
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception
from education_group.ddd.domain.exception import TrainingNotFoundException
from education_group.ddd.service.read import get_group_service, get_training_service
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.command import GetReportCommand
from program_management.ddd.domain import exception as program_exception
from program_management.ddd.domain.program_tree_version import version_label
from program_management.ddd.domain.report import Report
from program_management.ddd.domain.service.get_program_tree_version_for_tree import get_program_tree_version_for_tree
from program_management.ddd.domain.service.identity_search import TrainingIdentitySearch
from program_management.ddd.service.read import get_program_tree_service, get_program_tree_version_from_node_service
from program_management.forms import content as content_forms


class ContentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'base.change_link_data'
    raise_exception = True

    template_name = "program_management/content/update.html"

    def get(self, request, *args, **kwargs):
        obj = self.get_group_obj()
        version = self.get_version()
        context = {
            "content_formset": self.content_formset,
            "tabs": self.get_tabs(),
            "group_obj": obj,
            "cancel_url": self.get_cancel_url(),
            "version": version,
            "tree_different_versions": get_program_tree_version_for_tree(self.get_program_tree_obj().get_all_nodes()),
            "training_obj": self.get_training_obj() if obj.is_training() else None,
            "version_label": version_label(version.entity_id) if version else ''

        }
        return render(request, self.template_name, context)

    def get_version(self) -> Optional['ProgramTreeVersion']:
        try:
            get_cmd = command_program_management.GetProgramTreeVersionFromNodeCommand(
                code=self.kwargs['code'],
                year=self.kwargs['year']
            )
            return get_program_tree_version_from_node_service.get_program_tree_version_from_node(get_cmd)
        except program_exception.ProgramTreeVersionNotFoundException:
            return None

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Content"),
                "active": True,
                "display": True,
                "include_html": "program_management/content/block/panel_content.html"
            },
        ]

    def post(self, request, *args, **kwargs):
        if self.content_formset.is_valid():
            try:
                cmd, updated_links = self.content_formset.save()
                report = message_bus_instance.invoke(GetReportCommand(from_transaction_id=cmd.transaction_id))
                if report:
                    self.display_report_warning(report)
                success_messages = self.get_success_msg_updated_links()
                display_success_messages(request, success_messages, extra_tags='safe')
                check_formations_impacted_by_update(self.get_group_obj().code,
                                                    self.get_group_obj().year, request,
                                                    self.get_group_obj().type)
                return HttpResponseRedirect(self.get_success_url())
            except InvalidFormException:
                pass

        display_error_messages(self.request, self._get_default_error_messages())
        return self.get(request, *args, **kwargs)

    def display_report_warning(self, report: 'Report') -> None:
        display_warning_messages(self.request, list({str(warning) for warning in report.get_warnings()}))

    def get_success_url(self) -> str:
        get_data = {'path': self.request.GET['path_to']} if self.request.GET.get('path_to') else {}
        return reverse_with_get(
            'element_content',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get=get_data
        )

    def get_cancel_url(self) -> str:
        return self.get_success_url()

    def get_attach_path(self) -> Optional['Path']:
        return self.request.GET.get('path_to') or None

    @cached_property
    def content_formset(self) -> 'content_forms.ContentFormSet':
        return content_forms.ContentFormSet(
            self.request.POST or None,
            initial=self._get_content_formset_initial_values(),
            form_kwargs=[
                {'parent_obj': self.get_program_tree_obj().root_node, 'child_obj': child}
                for child in self.get_children()
            ]
        )

    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs["code"], year=int(self.kwargs["year"]))
            return get_group_service.get_group(get_cmd)
        except exception.GroupNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_program_tree_obj(self) -> 'ProgramTree':
        get_cmd = command_program_management.GetProgramTree(code=self.kwargs['code'], year=self.kwargs['year'])
        return get_program_tree_service.get_program_tree(get_cmd)

    @functools.lru_cache()
    def get_children(self) -> List['Node']:
        program_tree = self.get_program_tree_obj()
        return program_tree.root_node.children_as_nodes

    def get_success_msg_updated_links(self) -> List[str]:
        return [_("The link \"%(node)s\" has been updated.") % {"node": child} for child in self.get_children()]

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_content_formset_initial_values(self) -> List[Dict]:
        children_links = self.get_program_tree_obj().root_node.children
        return [{
            'relative_credits': link.relative_credits,
            'is_mandatory': link.is_mandatory,
            'link_type': link.link_type.name if link.link_type else None,
            'access_condition': link.access_condition,
            'block': link.block,
            'comment_fr': link.comment,
            'comment_en': link.comment_english
        } for link in children_links]

    @functools.lru_cache()
    def get_training_obj(self) -> 'Training':
        try:
            training_identity = TrainingIdentitySearch().get_from_program_tree_version_identity(
                self.get_version().entity_id)
            get_cmd = command.GetTrainingCommand(
                acronym=training_identity.acronym,
                year=training_identity.year
            )
            return get_training_service.get_training(get_cmd)
        except TrainingNotFoundException:
            raise Http404
