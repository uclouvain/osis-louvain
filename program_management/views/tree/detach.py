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

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

import osis_common.ddd.interface
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.cache import ElementCache
from base.views.common import display_error_messages, display_warning_messages
from base.views.common import display_success_messages
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import link
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.service.read import detach_warning_messages_service, get_program_tree_service
from program_management.ddd.service.write import detach_node_service
from program_management.forms.tree.detach import DetachNodeForm
from program_management.views.generic import GenericGroupElementYearMixin


class DetachNodeView(GenericGroupElementYearMixin, FormView):
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

    @property
    def parent_node(self) -> 'Node':
        return self.program_tree_obj.get_node("|".join([self.parent_id]))

    @property
    def child_node(self) -> 'Node':
        return self.program_tree_obj.get_node("|".join([self.parent_id, self.child_id_to_detach]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detach_node_command = command.DetachNodeCommand(path_where_to_detach=self.request.GET.get('path'), commit=False)
        try:
            detach_node_service.detach_node(detach_node_command)

            warning_messages = detach_warning_messages_service.detach_warning_messages(detach_node_command)
            display_warning_messages(self.request, warning_messages)

            context['confirmation_message'] = self.get_confirmation_msg()
        except MultipleBusinessExceptions as multiple_exceptions:
            messages = [e.message for e in multiple_exceptions.exceptions]
            display_error_messages(self.request, messages)

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
                'child': self.child_node,
                'parent': self.parent_node,
        }

    def get_confirmation_msg(self):
        return _("Are you sure you want to detach %(child)s ?") % {"child": self.child_node}

    def get_success_url(self):
        # We can just reload the page
        return
