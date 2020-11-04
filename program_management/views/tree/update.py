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
from typing import List, Dict

from django import shortcuts
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.forms.exceptions import InvalidFormException
from base.models.enums.link_type import LinkTypes
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import node
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.repositories import node as node_repository
from program_management.ddd.service.read import get_program_tree_service
from program_management.forms.content import ContentFormSet


class UpdateLinkView(AjaxPermissionRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "tree/link_update_inner.html"
    permission_required = "base.change_link_data"
    form_class = ContentFormSet

    def get_permission_object(self):
        return shortcuts.get_object_or_404(GroupYear, element__pk=self.program_tree.root_node.pk)

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Content"),
                "active": True,
                "display": True,
                "include_html": "program_management/content/block/panel_content.html"
            },
        ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["node"] = self.child_node
        context_data["tabs"] = self.get_tabs()
        context_data["content_formset"] = context_data.pop("form")
        return context_data

    def form_valid(self, form: ContentFormSet):
        try:
            form.save()
            display_success_messages(self.request, self.get_success_message())
            return super().form_valid(form)
        except InvalidFormException:
            return self.form_invalid(form)

    @cached_property
    def parent_node(self) -> 'Node':
        return self.program_tree.root_node

    @cached_property
    def child_node(self) -> 'Node':
        node_identity = node.NodeIdentity(self.kwargs.get('child_code'), self.kwargs.get('child_year'))
        return node_repository.NodeRepository.get(node_identity)

    @cached_property
    def link(self) -> 'Link':
        return self.program_tree.get_first_link_occurence_using_node(child_node=self.child_node)

    @cached_property
    def program_tree(self) -> ProgramTree:
        return get_program_tree_service.get_program_tree(command.GetProgramTree(
            code=self.kwargs.get('parent_code'), year=self.kwargs.get('parent_year')
        ))

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            form_kwargs=self.get_form_kwargs(),
            initial=self._get_initial_form_kwargs(self.link),
            data=self.request.POST or None
        )

    def _get_initial_form_kwargs(self, obj):
        return [{
            'comment_fr': obj.comment,
            'comment_en': obj.comment_english,
            'access_condition': obj.access_condition,
            'is_mandatory': obj.is_mandatory,
            'link_type': obj.link_type.name if isinstance(obj.link_type, LinkTypes) else obj.link_type,
            'block': obj.block,
            'credits': obj.child.credits,
            'code': obj.child.code,
            'relative_credits': obj.relative_credits
        }]

    def get_form_kwargs(self) -> List[Dict]:
        return [{'parent_obj': self.parent_node, 'child_obj': self.child_node}]

    def get_success_message(self):
        return _("The link \"%(node)s\" has been updated.") % {"node": self.child_node}

    def get_success_url(self):
        return
