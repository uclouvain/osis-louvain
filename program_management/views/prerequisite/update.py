##############################################################################
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

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.ddd.utils.validation_message import MessageLevel
from program_management.ddd.repositories import persist_tree
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.forms.prerequisite import PrerequisiteForm
from program_management.models.enums.node_type import NodeType
from program_management.views.generic import LearningUnitGenericUpdateView


class LearningUnitPrerequisite(LearningUnitGenericUpdateView):
    template_name = "learning_unit/tab_prerequisite_update.html"
    form_class = PrerequisiteForm

    def dispatch(self, request, *args, **kwargs):
        self.check_can_update_prerequisite()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        node = self._get_learning_unit_year_node()
        form_kwargs["program_tree"] = self.program_tree
        form_kwargs["node"] = node
        form_kwargs["initial"] = {
            "prerequisite_string": str(node.prerequisite)
        }
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["show_prerequisites"] = True
        return context

    def form_valid(self, form):
        node = self._get_learning_unit_year_node()
        messages = self.program_tree.set_prerequisite(form.cleaned_data["prerequisite_string"], node)
        error_messages = [msg for msg in messages if msg.level == MessageLevel.ERROR]
        if error_messages:
            raise PermissionDenied([msg.message for msg in error_messages])
        persist_tree.persist(self.program_tree)
        return super().form_valid(form)

    def _get_learning_unit_year_node(self):
        node = self.program_tree.get_node_by_id_and_type(
            int(self.kwargs["learning_unit_year_id"]),
            NodeType.LEARNING_UNIT
        )
        if node is None:
            raise Http404('No learning unit match the given query')
        return node

    #  FIXME refactor permission with new permission module
    def check_can_update_prerequisite(self):
        validator = AuthorizedRootTypeForPrerequisite(self.program_tree.root_node)
        if not validator.is_valid():
            raise PermissionDenied([msg.message for msg in validator.error_messages])

    def get_success_message(self, cleaned_data):
        return _("Prerequisites saved.")

    def get_success_url(self):
        return reverse("learning_unit_prerequisite", args=[self.kwargs["root_id"],
                                                           self.kwargs["learning_unit_year_id"]])
