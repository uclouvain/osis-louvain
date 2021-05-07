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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import functools
from typing import Optional, Dict

from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.forms.exceptions import InvalidFormException
from base.models.enums import education_group_categories
from base.views.common import display_warning_messages
from base.views.mixins import AjaxTemplateMixin
from education_group.models.group_year import GroupYear
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.command import GetReportCommand
from program_management.ddd.domain import program_tree_version
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.domain.report import Report
from program_management.ddd.service.read import get_program_tree_version_service, \
    get_report_service
from program_management.forms.fill_content import FillTransitionContentForm


class FillTransitionVersionContentView(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "tree_version/fill_content_inner.html"
    form_class = FillTransitionContentForm

    def get_context_data(self, **kwargs) -> Dict:
        context_data = super().get_context_data(**kwargs)
        context_data["tree_version"] = self.transition_tree
        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["transition_tree"] = self.transition_tree
        form_kwargs["last_year_transition_tree"] = self.last_year_transition_tree
        form_kwargs["same_version_tree"] = self.same_version_tree
        form_kwargs["last_year_same_version_tree"] = self.last_year_same_version_tree
        return form_kwargs

    def form_valid(self, form: 'FillTransitionContentForm'):
        try:
            transaction_id = form.save()
            report = message_bus_instance.invoke(GetReportCommand(from_transaction_id=transaction_id))
            if report:
                self.display_report_warning(report)
            return super().form_valid(form)
        except InvalidFormException:
            return self.form_invalid(form)

    def get_success_url(self) -> str:
        return ""

    def display_report_warning(self, report: 'Report') -> None:
        display_warning_messages(self.request, list({str(warning) for warning in report.get_warnings()}))

    def get_success_message(self, cleaned_data) -> str:
        return _("%(title)s in %(year)s has been filled") % {
            "title": self.transition_tree.official_name,
            "year": self.transition_tree.academic_year
        }

    def get_permission_required(self):
        if self.get_permission_object().education_group_type.category == education_group_categories.TRAINING:
            return ("base.fill_training_version",)
        return ("base.fill_minitraining_version",)

    @functools.lru_cache()
    def get_permission_object(self) -> GroupYear:
        return get_object_or_404(
            GroupYear,
            academic_year__year=self.kwargs['year'],
            acronym=self.kwargs['acronym'],
            educationgroupversion__version_name=self.kwargs['version_name'],
            educationgroupversion__transition_name=self.kwargs['transition_name'],
        )

    @cached_property
    def transition_tree(self) -> 'ProgramTreeVersion':
        return get_program_tree_version_service.get_program_tree_version(
            command.GetProgramTreeVersionCommand(
                year=self.kwargs['year'],
                acronym=self.kwargs['acronym'],
                version_name=self.kwargs['version_name'],
                transition_name=self.kwargs['transition_name']
            )
        )

    @cached_property
    def last_year_transition_tree(self) -> Optional['ProgramTreeVersion']:
        return get_program_tree_version_service.get_program_tree_version(
            command.GetProgramTreeVersionCommand(
                year=self.kwargs['year'] - 1,
                acronym=self.kwargs['acronym'],
                version_name=self.kwargs['version_name'],
                transition_name=self.kwargs['transition_name']
            )
        )

    @cached_property
    def same_version_tree(self) -> 'ProgramTreeVersion':
        return get_program_tree_version_service.get_program_tree_version(
            command.GetProgramTreeVersionCommand(
                year=self.kwargs['year'],
                acronym=self.kwargs['acronym'],
                version_name=self.kwargs['version_name'],
                transition_name=program_tree_version.NOT_A_TRANSITION
            )
        )

    @cached_property
    def last_year_same_version_tree(self) -> 'ProgramTreeVersion':
        return get_program_tree_version_service.get_program_tree_version(
            command.GetProgramTreeVersionCommand(
                year=self.kwargs['year'] - 1,
                acronym=self.kwargs['acronym'],
                version_name=self.kwargs['version_name'],
                transition_name=program_tree_version.NOT_A_TRANSITION
            )
        )
