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
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from base.models.enums import education_group_categories
from base.views.common import display_success_messages, display_error_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.ddd.domain.exception import TrainingHaveLinkWithEPC, \
    TrainingHaveEnrollments
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import ProgramTreeNonEmpty, NodeHaveLinkException, \
    ProgramTreeVersionNotFoundException, CannotDeleteSpecificVersionDueToTransitionVersionEndDate
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import delete_all_specific_versions_service
from program_management.formatter import format_program_tree_complete_title


class TreeVersionDeleteView(AjaxPermissionRequiredMixin, AjaxTemplateMixin, DeleteView):
    template_name = "tree_version/delete_inner.html"

    def get_object(self, queryset=None) -> 'ProgramTreeVersion':
        try:
            return ProgramTreeVersionRepository.get(self.tree_version_identity)
        except ProgramTreeVersionNotFoundException:
            raise Http404

    @cached_property
    def node_identity(self) -> 'NodeIdentity':
        return NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])

    @cached_property
    def tree_version_identity(self) -> 'ProgramTreeVersionIdentity':
        return ProgramTreeVersionIdentitySearch().get_from_node_identity(self.node_identity)

    def delete(self, request, *args, **kwargs):
        cmd_delete = command_program_management.DeletePermanentlyTreeVersionCommand(
            acronym=self.tree_version_identity.offer_acronym,
            version_name=self.tree_version_identity.version_name,
            transition_name=self.tree_version_identity.transition_name,
        )
        try:
            delete_all_specific_versions_service.delete_permanently_tree_version(cmd_delete)
            display_success_messages(request, self.get_success_message())
            return self._ajax_response() or HttpResponseRedirect(self.get_success_url())
        except (
                ProgramTreeNonEmpty,
                NodeHaveLinkException,
                TrainingHaveLinkWithEPC,
                TrainingHaveEnrollments,
                CannotDeleteSpecificVersionDueToTransitionVersionEndDate
        ) as e:
            display_error_messages(request, e.message)
            return render(request, self.template_name, {})

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'confirmation_message': self.get_confirmation_message(),
        }

    def get_confirmation_message(self) -> str:
        return _("Are you sure you want to delete %(object)s ?") % {
            'object': format_program_tree_complete_title(self.get_object(), translation.get_language()),
        }

    def get_success_message(self):
        if self.tree_version_identity.version_name:
            version_transition_name = '[{}{}]'.format(self.tree_version_identity.version_name,
                                                      '-{}'.format(self.tree_version_identity.transition_name)
                                                      if self.tree_version_identity.transition_name else '')
        else:
            version_transition_name = '[{}]'.format(self.tree_version_identity.transition_name) \
                if self.tree_version_identity.transition_name else ''
        return _("The program tree version %(offer_acronym)s%(version_name)s has been deleted.") % {
            'offer_acronym': self.tree_version_identity.offer_acronym,
            'version_name': version_transition_name,
        }

    def get_success_url(self) -> str:
        return reverse('version_program')

    def get_permission_required(self):
        if self.get_permission_object().education_group_type.category == education_group_categories.TRAINING:
            return ("program_management.delete_permanently_training_version",)
        return ("program_management.delete_permanently_minitraining_version",)

    def get_permission_object(self):
        return get_object_or_404(
            GroupYear.objects.select_related('education_group_type', 'academic_year', 'management_entity'),
            academic_year__year=self.node_identity.year,
            partial_acronym=self.node_identity.code,
        )
