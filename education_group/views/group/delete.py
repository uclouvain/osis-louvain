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
from django.utils.translation import gettext_lazy as _

from django.views.generic import DeleteView

from base.views.common import display_success_messages, display_error_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.ddd.business_types import *
from education_group.ddd import command
from education_group.ddd.domain.exception import GroupNotFoundException
from education_group.ddd.service.read import get_group_service
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.domain.exception import ProgramTreeNonEmpty, NodeHaveLinkException
from program_management.ddd.service.write import delete_all_program_tree_service


class GroupDeleteView(PermissionRequiredMixin, AjaxTemplateMixin, DeleteView):
    template_name = "education_group_app/group/delete_inner.html"
    permission_required = 'base.delete_all_group'

    def get_object(self, queryset=None) -> 'Group':
        try:
            cmd = command.GetGroupCommand(code=self.kwargs['code'], year=self.kwargs['year'])
            return get_group_service.get_group(cmd)
        except GroupNotFoundException:
            raise Http404

    def delete(self, request, *args, **kwargs):
        try:
            cmd_delete = command_program_management.DeleteAllProgramTreeCommand(code=self.kwargs['code'])
            delete_all_program_tree_service.delete_all_program_tree(cmd_delete)
            display_success_messages(request, self.get_success_message())
            return self._ajax_response() or HttpResponseRedirect(self.get_success_url())
        except (ProgramTreeNonEmpty, NodeHaveLinkException,) as e:
            display_error_messages(request, e.message)
            return render(request, self.template_name, {})

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'confirmation_message': self.get_confirmation_message(),
        }

    def get_confirmation_message(self) -> str:
        return _("Are you sure you want to delete %(code)s - %(title)s ?") % {
            'code': self.kwargs['code'],
            'title': self.get_object().titles.title_fr
        }

    def get_success_message(self):
        return _("The group %(code)s has been deleted.") % {'code': self.kwargs['code']}

    def get_success_url(self) -> str:
        return reverse('version_program')

    def get_permission_object(self):
        return get_object_or_404(
            GroupYear.objects.select_related('education_group_type', 'academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )
