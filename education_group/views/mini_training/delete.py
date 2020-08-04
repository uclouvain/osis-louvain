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
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.views.generic import DeleteView

from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.ddd.business_types import *

from education_group.ddd import command
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


class MiniTrainingDeleteView(PermissionRequiredMixin, AjaxTemplateMixin, DeleteView):
    template_name = "education_group_app/mini_training/delete_inner.html"
    permission_required = 'base.delete_all_minitraining'

    def get_object(self, queryset=None) -> 'ProgramTreeVersion':
        pass
        # try:
        #     node_identity = NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])
        #     program_tree_version_identity = ProgramTreeVersionIdentitySearch().get_from_node_identity(node_identity)
        #     return ProgramTreeVersionRepository.get(program_tree_version_identity)
        # except ProgramTreeVersionNotFound:
        #     raise Http404

    def get_mini_training(self) -> 'MiniTraining':
        pass
        # try:
        #     cmd = command.GetMiniTraining(acronym="", year=self.kwargs['year'])
        #     return get_mini_training_service.get_mini_training(cmd)
        # except MiniTrainingNotFoundException:
        #     raise Http404

    def delete(self, request, *args, **kwargs):
        # Call delete program_tree_version service ()
        display_success_messages(request, self.get_success_message())
        return self._ajax_response() or HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'confirmation_message': self.get_confirmation_message(),
        }

    def get_confirmation_message(self) -> str:
        return _("Are you sure you want to delete %(code)s - %(title)s ?") % {
            'code': self.kwargs['code'],
            'title': self.get_mini_training().titles.title_fr
        }

    def get_success_message(self):
        return _("The mini-training %(code)s has been deleted.") % {'code': self.kwargs['code']}

    def get_success_url(self) -> str:
        return reverse('version_program')

    def get_permission_object(self):
        return get_object_or_404(
            GroupYear.objects.select_related('education_group_type', 'academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )
