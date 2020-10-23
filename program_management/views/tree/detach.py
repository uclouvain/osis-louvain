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
from typing import Union

import osis_common.ddd.interface
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.utils.cache import ElementCache
from base.views.common import display_error_messages, display_warning_messages
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.ddd import command as command_education_group
from education_group.ddd.domain.group import Group
from education_group.ddd.service.read import get_group_service
from education_group.templatetags.academic_year_display import display_as_academic_year
from learning_unit.ddd import command as command_learning_unit
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear
from learning_unit.ddd.service.read import get_learning_unit_year_service
from osis_common.ddd import interface
from program_management.ddd import command
from program_management.ddd.domain import link
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch, ProgramTreeVersionIdentitySearch
from program_management.ddd.service.read import detach_warning_messages_service, get_program_tree_service
from program_management.ddd.service.write import detach_node_service
from program_management.forms.tree.detach import DetachNodeForm
from program_management.models.enums.node_type import NodeType
from program_management.views.generic import GenericGroupElementYearMixin


class DetachNodeView(GenericGroupElementYearMixin, AjaxTemplateMixin, FormView):
    template_name = "tree/detach_confirmation_inner.html"
    form_class = DetachNodeForm

    permission_required = 'base.can_detach_node'

    @property
    def parent_id(self):
        return self.path_to_detach.split('|')[-2]

    @property
    def child_id_to_detach(self):
        return self.path_to_detach.split('|')[-1]

    @property
    def path_to_detach(self):
        return self.request.GET.get('path')

    @property
    def root_id(self):
        return self.path_to_detach.split('|')[0]

    @cached_property
    def program_tree_obj(self):
        node_identity = NodeIdentitySearch().get_from_element_id(int(self.parent_id))
        cmd = command.GetProgramTree(code=node_identity.code, year=node_identity.year)
        return get_program_tree_service.get_program_tree(cmd)

    @cached_property
    def child_obj(self) -> Union['Group', 'LearningUnitYear']:
        child_node = self.program_tree_obj.get_node("|".join([self.parent_id, self.child_id_to_detach]))
        if child_node.node_type == NodeType.LEARNING_UNIT:
            cmd = command_learning_unit.GetLearningUnitYearCommand(code=child_node.code, year=child_node.year)
            return get_learning_unit_year_service.get_learning_unit_year(cmd)
        cmd = command_education_group.GetGroupCommand(code=child_node.code, year=child_node.year)
        return get_group_service.get_group(cmd)

    @cached_property
    def child_version_identity(self) -> Union['ProgramTreeVersionIdentity', None]:
        try:
            child_node = self.program_tree_obj.get_node("|".join([self.parent_id, self.child_id_to_detach]))
            return ProgramTreeVersionIdentitySearch().get_from_node_identity(child_node.entity_id)
        except interface.BusinessException:
            return None

    @cached_property
    def parent_group_obj(self) -> 'Group':
        cmd = command_education_group.GetGroupCommand(
            code=self.program_tree_obj.root_node.code,
            year=self.program_tree_obj.root_node.year
        )
        return get_group_service.get_group(cmd)

    @cached_property
    def parent_version_identity(self) -> Union['ProgramTreeVersionIdentity', None]:
        try:
            entity_id = self.program_tree_obj.root_node.entity_id
            return ProgramTreeVersionIdentitySearch().get_from_node_identity(entity_id)
        except interface.BusinessException:
            return None

    def get_context_data(self, **kwargs):
        context = super(DetachNodeView, self).get_context_data(**kwargs)
        detach_node_command = command.DetachNodeCommand(path_where_to_detach=self.request.GET.get('path'), commit=False)
        try:
            link_to_detach_id = detach_node_service.detach_node(detach_node_command)
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            display_error_messages(self.request, business_exception.messages)
        else:
            warning_messages = detach_warning_messages_service.detach_warning_messages(detach_node_command)
            display_warning_messages(self.request, warning_messages)

            link_to_detach = self.get_object()
            context['confirmation_message'] = self.get_confirmation_msg()
        return context

    def get_initial(self):
        return {
            **super().get_initial(),
            'path': self.path_to_detach
        }

    def get_object(self):
        obj = self.model.objects.get(
            parent_element_id=self.parent_id,
            child_element_id=self.child_id_to_detach
        )
        return obj

    def form_valid(self, form):
        success_msg = self.get_success_msg()
        try:
            link_entity_id = form.save()
        except osis_common.ddd.interface.BusinessExceptions as business_exception:
            display_error_messages(self.request, business_exception.messages)
            return self.form_invalid(form)

        display_success_messages(self.request, success_msg)
        self._remove_element_from_clipboard_if_stored(link_entity_id)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super(DetachNodeView, self).form_invalid(form)

    def _remove_element_from_clipboard_if_stored(self, link_entity_id: link.LinkIdentity):
        element_cache = ElementCache(self.request.user)
        if element_cache.equals_element(link_entity_id.child_code, link_entity_id.child_year):
            element_cache.clear()

    def get_success_msg(self):
        return _("\"%(child)s\" has been detached from \"%(parent)s\"") % {
                'child': self._get_child_node_str(),
                'parent': self._get_parent_node_str(),
        }

    def get_confirmation_msg(self):
        return _("Are you sure you want to detach %(child)s ?") % {"child": self._get_child_node_str()}

    def _get_child_node_str(self):
        return "%(code)s %(abbreviated_title)s%(version)s - %(year)s" % {
            "code": self.child_obj.acronym if isinstance(self.child_obj, LearningUnitYear) else self.child_obj.code,
            "abbreviated_title": '' if isinstance(self.child_obj, LearningUnitYear)
            else "- " + self.child_obj.abbreviated_title,
            "version": "[{}]".format(self.child_version_identity.version_name)
                       if self.child_version_identity and not self.child_version_identity.is_standard() else "",
            "year": display_as_academic_year(self.child_obj.year)
        }

    def _get_parent_node_str(self):
        return "%(code)s - %(abbreviated_title)s%(version)s - %(year)s" % {
            "code": self.parent_group_obj.code,
            "abbreviated_title": self.parent_group_obj.abbreviated_title,
            "version": "[{}]".format(self.parent_version_identity.version_name)
                       if self.parent_version_identity and not self.parent_version_identity.is_standard() else "",
            "year": self.parent_group_obj.academic_year
        }

    def get_success_url(self):
        # We can just reload the page
        return
