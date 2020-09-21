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
from django import shortcuts
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

import osis_common
from base.models.enums.link_type import LinkTypes
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.models.group_year import GroupYear
from osis_common.ddd.interface import BusinessException
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.domain import node
from program_management.ddd.domain.node import NodeGroupYear
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories import node as node_repository
from program_management.ddd.service.read import get_program_tree_service
from program_management.forms.tree.update import UpdateLinkForm


class UpdateLinkView(AjaxPermissionRequiredMixin, AjaxTemplateMixin, SuccessMessageMixin, FormView):
    template_name = "tree/link_update_inner.html"
    permission_required = "base.change_link_data"
    form_class = UpdateLinkForm

    @cached_property
    def parent_node(self) -> dict:
        return {"element_code": self.kwargs.get('parent_code'), "element_year": self.kwargs.get('parent_year')}

    @cached_property
    def node_to_update(self) -> dict:
        return {"element_code": self.kwargs.get('child_code'), "element_year": self.kwargs.get('child_year')}

    @cached_property
    def program_tree(self) -> ProgramTree:
        return get_program_tree_service.get_program_tree(command.GetProgramTree(
            code=self.parent_node['element_code'], year=self.parent_node['element_year']
        ))

    def get_permission_object(self):
        return shortcuts.get_object_or_404(GroupYear, element__pk=self.program_tree.root_node.pk)

    def get_form_kwargs(self) -> dict:
        return {
            'parent_node_code': self.parent_node["element_code"],
            'parent_node_year': self.parent_node["element_year"],
            'node_to_update_code': self.node_to_update["element_code"],
            'node_to_update_year': self.node_to_update["element_year"],
        }

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), data=self.request.POST or None)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["is_parent_a_minor_major_option_list_choice"] = self._is_parent_a_minor_major_option_list_choice()
        context_data["node"] = node_repository.NodeRepository.get(node.NodeIdentity(
            self.node_to_update["element_code"], self.node_to_update["element_year"]
        ))
        self._format_title_with_version(context_data["node"])

        node_elem = context_data["node"]
        link = self.program_tree.get_first_link_occurence_using_node(child_node=node_elem)
        context_data['form'].initial = self._get_initial_form_kwargs(link)
        context_data['has_group_year_form'] = isinstance(node_elem, NodeGroupYear)

        return context_data

    def form_valid(self, form: UpdateLinkForm):
        try:
            link = form.save()
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            form.add_error(field=None, error=business_exception.messages)
            return self.form_invalid(form)
        messages = self._append_success_message(link.entity_id.child_code)
        display_success_messages(self.request, messages)
        return super().form_valid(form)

    def _append_success_message(self, child_code):
        messages = []
        messages.append(_("\"%(child)s\" has been successfully updated") % {"child": child_code})
        return messages

    def _get_initial_form_kwargs(self, obj):
        return {
            'comment': obj.comment,
            'comment_english': obj.comment_english,
            'access_condition': obj.access_condition,
            'is_mandatory': obj.is_mandatory,
            'link_type': obj.link_type.name if isinstance(obj.link_type, LinkTypes) else obj.link_type,
            'block': obj.block,
            'credits': obj.child.credits,
            'code': obj.child.code,
            'relative_credits': obj.relative_credits
        }

    def _format_title_with_version(self, node):
        node_identity = NodeIdentity(code=self.node_to_update["element_code"], year=self.node_to_update["element_year"])
        try:
            tree_version = ProgramTreeVersionIdentitySearch().get_from_node_identity(node_identity)
            node.version = tree_version.version_name
            node.title = "{}[{}]".format(node.title, node.version) if node.version else node.title
        except BusinessException:
            pass

    def _is_parent_a_minor_major_option_list_choice(self):
        parent = self.program_tree.root_node
        return parent.is_minor_major_list_choice() or parent.is_option_list_choice()

    def get_success_url(self):
        return
