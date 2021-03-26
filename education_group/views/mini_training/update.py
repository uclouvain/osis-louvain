#############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#############################################################################
import functools
from typing import List, Dict, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils import operator
from base.utils.urls import reverse_with_get
from base.views.common import display_success_messages, display_warning_messages, display_error_messages, \
    check_formations_impacted_by_update
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception
from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.ddd.service.read import get_group_service, get_mini_training_service
from education_group.forms import mini_training as mini_training_forms
from education_group.models.group_year import GroupYear
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.views.proxy.read import Tab
from osis_common.utils.models import get_object_or_none
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception as program_management_exception
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.service.write import delete_mini_training_with_program_tree_service, \
    postpone_mini_training_and_program_tree_modifications_service


class MiniTrainingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'base.change_minitraining'
    raise_exception = True

    template_name = "education_group_app/mini_training/upsert/update.html"

    @transaction.non_atomic_requests
    def get(self, request, *args, **kwargs):
        context = {
            "tabs": self.get_tabs(),
            "mini_training_form": self.mini_training_form,
            "mini_training_obj": self.get_mini_training_obj(),
            "cancel_url": self.get_cancel_url(),
            "type_text": self.get_mini_training_obj().type.value
        }
        return render(request, self.template_name, context)

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):
        if self.mini_training_form.is_valid():
            deleted_trainings = self.delete_mini_training()
            if not self.mini_training_form.errors:
                update_trainings = list(set(self.update_mini_training()))
                update_trainings.sort(key=lambda identity: identity.year)
            if not self.mini_training_form.errors:
                success_messages = self.get_success_msg_updated_mini_trainings(update_trainings)
                success_messages += self.get_success_msg_deleted_mini_trainings(update_trainings)
                display_success_messages(request, success_messages, extra_tags='safe')
                check_formations_impacted_by_update(self.get_mini_training_obj().code,
                                                    self.get_mini_training_obj().year,
                                                    request, self.get_mini_training_obj().type)
                return HttpResponseRedirect(self.get_success_url())
        display_error_messages(self.request, self._get_default_error_messages())
        return self.get(request, *args, **kwargs)

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/mini_training/upsert/identification_form.html"
            }
        ]

    def get_success_url(self) -> str:
        get_data = {'path': self.request.GET['path']} if self.request.GET.get('path') else {}
        return reverse_with_get(
            'element_identification',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get=get_data
        )

    def get_cancel_url(self) -> str:
        return self.get_success_url()

    def update_mini_training(self) -> List['MiniTrainingIdentity']:
        try:
            update_command = self._convert_form_to_update_mini_training_command(self.mini_training_form)
            return postpone_mini_training_and_program_tree_modifications_service. \
                postpone_mini_training_and_program_tree_modifications(update_command)
        except MultipleBusinessExceptions as multiple_exceptions:
            for e in multiple_exceptions.exceptions:
                if isinstance(e, exception.ContentConstraintTypeMissing):
                    self.mini_training_form.add_error("constraint_type", e.message)
                elif isinstance(e, exception.ContentConstraintMinimumMaximumMissing) or \
                        isinstance(e, exception.ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum):
                    self.mini_training_form.add_error("min_constraint", e.message)
                    self.mini_training_form.add_error("max_constraint", "")
                elif isinstance(e, exception.ContentConstraintMinimumInvalid):
                    self.mini_training_form.add_error("min_constraint", e.message)
                elif isinstance(e, exception.ContentConstraintMaximumInvalid):
                    self.mini_training_form.add_error("max_constraint", e.message)
                else:
                    self.mini_training_form.add_error(None, e.message)
        except exception.MiniTrainingCopyConsistencyException as e:
            display_warning_messages(self.request, e.message)
            return [
                MiniTrainingIdentity(acronym=self.get_mini_training_obj().acronym, year=year)
                for year in range(self.get_mini_training_obj().year, e.conflicted_fields_year)
            ]
        return []

    def delete_mini_training(self) -> List['MiniTrainingIdentity']:
        end_year = self.mini_training_form.cleaned_data["end_year"]
        if not end_year:
            return []
        try:
            delete_command = self._convert_form_to_delete_mini_trainings_command(self.mini_training_form)
            return delete_mini_training_with_program_tree_service.delete_mini_training_with_program_tree(delete_command)
        except (
                program_management_exception.ProgramTreeNonEmpty,
                exception.MiniTrainingHaveLinkWithEPC,
                exception.MiniTrainingHaveEnrollments,
                program_management_exception.NodeHaveLinkException,
                program_management_exception.CannotDeleteStandardDueToTransitionVersionEndDate,
                program_management_exception.CannotDeleteStandardDueToSpecificVersionEndDate
        ) as e:
            self.mini_training_form.add_error("end_year", "")
            self.mini_training_form.add_error(
                None,
                _("Impossible to put end date to %(end_year)s: %(msg)s") % {
                    "msg": e.message,
                    "end_year": end_year
                }
            )
        return []

    def get_attach_path(self) -> Optional['Path']:
        return self.request.GET.get('path_to') or None

    @cached_property
    def mini_training_form(self) -> 'mini_training_forms.UpdateMiniTrainingForm':
        return mini_training_forms.UpdateMiniTrainingForm(
            self.request.POST or None,
            user=self.request.user,
            year=self.kwargs['year'],
            mini_training_type=self.get_mini_training_obj().type.name,
            attach_path=self.get_attach_path(),
            initial=self._get_mini_training_form_initial_values()
        )

    def get_permission_object(self) -> Optional[GroupYear]:
        return get_object_or_none(
            GroupYear.objects.select_related('academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )

    def get_mini_training_obj(self) -> 'MiniTraining':
        try:
            get_cmd = command.GetMiniTrainingCommand(acronym=self.kwargs["acronym"], year=int(self.kwargs["year"]))
            return get_mini_training_service.get_mini_training(get_cmd)
        except exception.MiniTrainingNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs["code"], year=int(self.kwargs["year"]))
            return get_group_service.get_group(get_cmd)
        except exception.TrainingNotFoundException:
            raise Http404

    def get_success_msg_updated_mini_trainings(
            self,
            mini_training_identites: List["MiniTrainingIdentity"]) -> List[str]:
        return [self._get_success_msg_updated_mini_training(identity) for identity in mini_training_identites]

    def get_success_msg_deleted_mini_trainings(
            self,
            mini_trainings_identities: List['MiniTrainingIdentity']) -> List[str]:
        end_year = self.mini_training_form.cleaned_data["end_year"]
        last_identity = mini_trainings_identities[-1]
        is_new_end_year_lower_than_initial_one = operator.is_year_lower(
            end_year.year if end_year else None,
            self.mini_training_form.initial['end_year']
        )
        if is_new_end_year_lower_than_initial_one:
            delete_message = _(
                "Mini-Training %(acronym)s successfully deleted from %(academic_year)s."
            ) % {
                                 "acronym": last_identity.acronym,
                                 "academic_year": display_as_academic_year(
                                     self.mini_training_form.cleaned_data["end_year"].year + 1)
                             }
            return [delete_message]
        return []

    def _get_success_msg_updated_mini_training(self, mini_training_identity: 'MiniTrainingIdentity') -> str:
        link = reverse_with_get(
            'education_group_read_proxy',
            kwargs={'acronym': mini_training_identity.acronym, 'year': mini_training_identity.year},
            get={"tab": Tab.IDENTIFICATION.value}
        )
        return _("Mini-Training <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfully updated.") % {
            "link": link,
            "acronym": mini_training_identity.acronym,
            "academic_year": display_as_academic_year(mini_training_identity.year),
        }

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_mini_training_form_initial_values(self) -> Dict:
        mini_training_obj = self.get_mini_training_obj()
        group_obj = self.get_group_obj()

        form_initial_values = {
            "abbreviated_title": mini_training_obj.acronym,
            "code": mini_training_obj.code,
            "active": mini_training_obj.status.name,
            "schedule_type": mini_training_obj.schedule_type.name,
            "credits": mini_training_obj.credits,

            "constraint_type": group_obj.content_constraint.type.name
            if group_obj.content_constraint.type else None,
            "min_constraint": group_obj.content_constraint.minimum,
            "max_constraint": group_obj.content_constraint.maximum,

            "title_fr": mini_training_obj.titles.title_fr,
            "title_en": mini_training_obj.titles.title_en,
            "keywords": mini_training_obj.keywords,

            "management_entity": mini_training_obj.management_entity.acronym,
            "academic_year": mini_training_obj.year,
            "start_year": mini_training_obj.start_year,
            "end_year": mini_training_obj.end_year,
            "teaching_campus": group_obj.teaching_campus.name,

            "remark_fr": group_obj.remark.text_fr,
            "remark_en": group_obj.remark.text_en,
        }
        return form_initial_values

    def _convert_form_to_update_mini_training_command(
            self,
            form: mini_training_forms.UpdateMiniTrainingForm
    ) -> command_program_management.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand:
        cleaned_data = form.cleaned_data
        return command_program_management.PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand(
            abbreviated_title=cleaned_data['abbreviated_title'],
            code=cleaned_data['code'],
            year=cleaned_data['academic_year'],
            status=cleaned_data['status'],
            credits=cleaned_data['credits'],
            title_fr=cleaned_data['title_fr'],
            title_en=cleaned_data['title_en'],
            keywords=cleaned_data['keywords'],
            management_entity_acronym=cleaned_data['management_entity'],
            end_year=cleaned_data['end_year'].year if cleaned_data['end_year'] else None,
            teaching_campus_name=cleaned_data['teaching_campus']['name'],
            teaching_campus_organization_name=cleaned_data['teaching_campus']['organization_name'],
            constraint_type=cleaned_data['constraint_type'],
            min_constraint=cleaned_data['min_constraint'],
            max_constraint=cleaned_data['max_constraint'],
            remark_fr=cleaned_data['remark_fr'],
            remark_en=cleaned_data['remark_en'],
            organization_name=cleaned_data['teaching_campus']['organization_name'],
            schedule_type=cleaned_data["schedule_type"],
        )

    def _convert_form_to_delete_mini_trainings_command(
            self,
            mini_training_form: mini_training_forms.UpdateMiniTrainingForm
    ) -> command_program_management.DeleteMiniTrainingWithProgramTreeCommand:
        cleaned_data = mini_training_form.cleaned_data
        return command_program_management.DeleteMiniTrainingWithProgramTreeCommand(
            code=cleaned_data["code"],
            offer_acronym=cleaned_data["abbreviated_title"],
            version_name='',
            transition_name=NOT_A_TRANSITION,
            from_year=cleaned_data["end_year"].year + 1
        )
