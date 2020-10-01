# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
# ############################################################################
import functools
from typing import List, Dict, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.utils.urls import reverse_with_get
from base.views.common import display_success_messages, display_warning_messages, display_error_messages
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception
from education_group.ddd.domain.exception import TrainingCopyConsistencyException
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.service.read import get_training_service, get_group_service
from education_group.forms import training as training_forms
from education_group.models.group_year import GroupYear
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.views.proxy.read import Tab
from osis_common.utils.models import get_object_or_none
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception as program_management_exception
from program_management.ddd.domain.exception import Program2MEndDateShouldBeGreaterOrEqualThanItsFinalities
from program_management.ddd.service.write import delete_training_with_program_tree_service, \
    postpone_training_and_program_tree_modifications_service


class TrainingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'base.change_training'
    raise_exception = True

    template_name = "education_group_app/training/upsert/update.html"

    @transaction.non_atomic_requests
    def get(self, request, *args, **kwargs):
        context = {
            "tabs": self.get_tabs(),
            "training_form": self.training_form,
            "training_obj": self.get_training_obj(),
            "cancel_url": self.get_cancel_url(),
            "type_text": self.get_training_obj().type.value,
            "is_finality_types": self.get_training_obj().is_finality()
        }
        return render(request, self.template_name, context)

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):
        deleted_trainings = []
        updated_trainings = []

        if self.training_form.is_valid():
            deleted_trainings = self.delete_training()
            if not self.training_form.errors:
                updated_trainings = self.update_training()

            if not self.training_form.errors:
                success_messages = self.get_success_msg_updated_trainings(updated_trainings)
                success_messages += self.get_success_msg_deleted_trainings(deleted_trainings)
                display_success_messages(request, success_messages, extra_tags='safe')
                return HttpResponseRedirect(self.get_success_url())
        display_error_messages(self.request, self._get_default_error_messages())
        return self.get(request, *args, **kwargs)

    def get_tabs(self) -> List:
        tab_to_display = self.request.GET.get('tab', Tab.IDENTIFICATION.name)
        is_diploma_active = tab_to_display == Tab.DIPLOMAS_CERTIFICATES.name
        is_identification_active = not is_diploma_active
        return [
            {
                "text": _("Identification"),
                "active": is_identification_active,
                "display": True,
                "include_html": "education_group_app/training/upsert/training_identification_form.html"
            },
            {
                "text": _("Diplomas /  Certificates"),
                "active": is_diploma_active,
                "display": True,
                "include_html": "education_group_app/training/upsert/blocks/panel_diplomas_certificates_form.html"
            },
        ]

    def get_success_url(self) -> str:
        get_data = {'path': self.request.GET['path_to']} if self.request.GET.get('path_to') else {}
        return reverse_with_get(
            'element_identification',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get=get_data
        )

    def get_cancel_url(self) -> str:
        return self.get_success_url()

    def update_training(self) -> List['TrainingIdentity']:
        try:
            postpone_modification_command = self._convert_form_to_postpone_modification_cmd(self.training_form)
            return postpone_training_and_program_tree_modifications_service.\
                postpone_training_and_program_tree_modifications(postpone_modification_command)
        except exception.ContentConstraintTypeMissing as e:
            self.training_form.add_error("constraint_type", e.message)
        except (exception.ContentConstraintMinimumMaximumMissing,
                exception.ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum) as e:
            self.training_form.add_error("min_constraint", e.message)
            self.training_form.add_error("max_constraint", "")
        except Program2MEndDateShouldBeGreaterOrEqualThanItsFinalities as e:
            self.training_form.add_error("end_year", e.message)
        except TrainingCopyConsistencyException as e:
            display_warning_messages(self.request, e.message)
            return [
                TrainingIdentity(acronym=self.get_training_obj().acronym, year=year)
                for year in range(self.get_training_obj().year, e.conflicted_fields_year)
            ]
        return []

    def delete_training(self) -> List['TrainingIdentity']:
        end_year = self.training_form.cleaned_data["end_year"]
        if not end_year:
            return []
        try:
            delete_command = self._convert_form_to_delete_trainings_command(self.training_form)
            return delete_training_with_program_tree_service.delete_training_with_program_tree(delete_command)
        except (
            program_management_exception.ProgramTreeNonEmpty,
            exception.TrainingHaveLinkWithEPC,
            exception.TrainingHaveEnrollments,
            program_management_exception.CannotDeleteStandardDueToVersionEndDate
        ) as e:
            self.training_form.add_error("end_year", "")
            self.training_form.add_error(
                None,
                _("Impossible to put end date to %(end_year)s: %(msg)s") % {
                    "msg": e.message,
                    "end_year": end_year}
            )

        return []

    def get_attach_path(self) -> Optional['Path']:
        return self.request.GET.get('path_to') or None

    @cached_property
    def training_form(self) -> 'training_forms.UpdateTrainingForm':
        return training_forms.UpdateTrainingForm(
            self.request.POST or None,
            user=self.request.user,
            event_perm_obj=self.get_permission_object(),
            training_type=self.get_training_obj().type.name,
            attach_path=self.get_attach_path(),
            initial=self._get_training_form_initial_values()
        )

    @functools.lru_cache()
    def get_training_obj(self) -> 'Training':
        try:
            get_cmd = command.GetTrainingCommand(acronym=self.kwargs["title"], year=int(self.kwargs["year"]))
            return get_training_service.get_training(get_cmd)
        except exception.TrainingNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs["code"], year=int(self.kwargs["year"]))
            return get_group_service.get_group(get_cmd)
        except exception.TrainingNotFoundException:
            raise Http404

    def get_permission_object(self) -> Optional[GroupYear]:
        return get_object_or_none(
            GroupYear.objects.select_related('academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )

    def get_success_msg_updated_trainings(self, training_identites: List["TrainingIdentity"]) -> List[str]:
        return [self._get_success_msg_updated_training(identity) for identity in training_identites]

    def get_success_msg_deleted_trainings(self, trainings_identities: List['TrainingIdentity']) -> List[str]:
        return [self._get_success_msg_deleted_training(identity) for identity in trainings_identities]

    def _get_success_msg_updated_training(self, training_identity: 'TrainingIdentity') -> str:
        link = reverse_with_get(
            'education_group_read_proxy',
            kwargs={'acronym': training_identity.acronym, 'year': training_identity.year},
            get={"tab": Tab.IDENTIFICATION.value}
        )
        return _("Training <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfully updated.") % {
            "link": link,
            "acronym": training_identity.acronym,
            "academic_year": display_as_academic_year(training_identity.year),
        }

    def _get_success_msg_deleted_training(self, training_identity: 'TrainingIdentity') -> str:
        return _("Training %(acronym)s (%(academic_year)s) successfully deleted.") % {
            "acronym": training_identity.acronym,
            "academic_year": display_as_academic_year(training_identity.year)
        }

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_training_form_initial_values(self) -> Dict:
        training_obj = self.get_training_obj()
        group_obj = self.get_group_obj()

        form_initial_values = {
            "acronym": training_obj.acronym,
            "code": training_obj.code,
            "active": training_obj.status.name,
            "schedule_type": training_obj.schedule_type.name,
            "credits": training_obj.credits,

            "constraint_type": group_obj.content_constraint.type.name
            if group_obj.content_constraint.type else None,
            "min_constraint": group_obj.content_constraint.minimum,
            "max_constraint": group_obj.content_constraint.maximum,

            "title_fr": training_obj.titles.title_fr,
            "partial_title_fr": training_obj.titles.partial_title_fr,
            "title_en": training_obj.titles.title_en,
            "partial_title_en": training_obj.titles.partial_title_en,
            "keywords": training_obj.keywords,

            "academic_type": training_obj.academic_type.name,
            "duration": training_obj.duration,
            "duration_unit": training_obj.duration_unit.name if training_obj.duration_unit else None,
            "internship_presence": training_obj.internship_presence.name if training_obj.internship_presence else None,
            "is_enrollment_enabled": training_obj.is_enrollment_enabled,
            "has_online_re_registration": training_obj.has_online_re_registration,
            "has_partial_deliberation": training_obj.has_partial_deliberation,
            "has_admission_exam": training_obj.has_admission_exam,
            "has_dissertation": training_obj.has_dissertation,
            "produce_university_certificate": training_obj.produce_university_certificate,
            "decree_category": training_obj.decree_category.name if training_obj.decree_category else None,
            "rate_code": training_obj.rate_code.name if training_obj.rate_code else None,

            "main_language": training_obj.main_language.name,
            "english_activities": training_obj.english_activities.name if training_obj.english_activities else None,
            "other_language_activities": training_obj.other_language_activities.name
            if training_obj.other_language_activities else None,

            "main_domain": "{} - {}".format(training_obj.main_domain.decree_name, training_obj.main_domain.code)
            if training_obj.main_domain else None,
            "secondary_domains": training_obj.secondary_domains,
            "isced_domain": training_obj.isced_domain.entity_id.code if training_obj.isced_domain else None,
            "internal_comment": training_obj.internal_comment,

            "management_entity": training_obj.management_entity.acronym,
            "administration_entity": training_obj.administration_entity.acronym,
            "academic_year": training_obj.year,
            "start_year": training_obj.start_year,
            "end_year": training_obj.end_year,
            "teaching_campus": group_obj.teaching_campus.name,
            "enrollment_campus": training_obj.enrollment_campus.name,
            "other_campus_activities": training_obj.other_campus_activities.name
            if training_obj.other_language_activities else None,

            "can_be_funded": training_obj.funding.can_be_funded,
            "funding_direction": training_obj.funding.funding_orientation.name
            if training_obj.funding.funding_orientation else None,
            "can_be_international_funded": training_obj.funding.can_be_international_funded,
            "international_funding_orientation": training_obj.funding.international_funding_orientation.name
            if training_obj.funding.international_funding_orientation else None,

            "remark_fr": group_obj.remark.text_fr,
            "remark_english": group_obj.remark.text_en,

            "ares_code": training_obj.hops.ares_code if training_obj.hops else None,
            "ares_graca": training_obj.hops.ares_graca if training_obj.hops else None,
            "ares_authorization": training_obj.hops.ares_authorization if training_obj.hops else None,
            "code_inter_cfb": training_obj.co_graduation.code_inter_cfb,
            "coefficient": training_obj.co_graduation.coefficient.normalize()
            if training_obj.co_graduation.coefficient else None,

            "leads_to_diploma": training_obj.diploma.leads_to_diploma,
            "diploma_printing_title": training_obj.diploma.printing_title,
            "professional_title": training_obj.diploma.professional_title,
            "certificate_aims": [aim.code for aim in training_obj.diploma.aims]
        }

        return form_initial_values

    def _convert_form_to_postpone_modification_cmd(
            self,
            form: training_forms.UpdateTrainingForm
    ) -> command_program_management.PostponeTrainingAndRootGroupModificationWithProgramTreeCommand:
        cleaned_data = form.cleaned_data
        return command_program_management.PostponeTrainingAndRootGroupModificationWithProgramTreeCommand(
            postpone_from_acronym=cleaned_data['acronym'],
            postpone_from_year=cleaned_data['academic_year'].year,
            code=cleaned_data['code'],
            status=cleaned_data['active'],
            credits=cleaned_data['credits'],
            duration=cleaned_data['duration'],
            title_fr=cleaned_data['title_fr'],
            partial_title_fr=cleaned_data['partial_title_fr'],
            title_en=cleaned_data['title_en'],
            partial_title_en=cleaned_data['partial_title_en'],
            keywords=cleaned_data['keywords'],
            internship_presence=cleaned_data['internship_presence'],
            is_enrollment_enabled=cleaned_data['is_enrollment_enabled'],
            has_online_re_registration=cleaned_data['has_online_re_registration'],
            has_partial_deliberation=cleaned_data['has_partial_deliberation'],
            has_admission_exam=cleaned_data['has_admission_exam'],
            has_dissertation=cleaned_data['has_dissertation'],
            produce_university_certificate=cleaned_data['produce_university_certificate'],
            main_language=cleaned_data['main_language'],
            english_activities=cleaned_data['english_activities'],
            other_language_activities=cleaned_data['other_language_activities'],
            internal_comment=cleaned_data['internal_comment'],
            main_domain_code=cleaned_data['main_domain'].code if cleaned_data.get('main_domain') else None,
            main_domain_decree=cleaned_data['main_domain'].decree.name
            if cleaned_data.get('main_domain') else None,
            secondary_domains=[
                (obj.decree.name, obj.code) for obj in cleaned_data.get('secondary_domains', list())
            ],
            isced_domain_code=cleaned_data['isced_domain'].code if cleaned_data.get('isced_domain') else None,
            management_entity_acronym=cleaned_data['management_entity'],
            administration_entity_acronym=cleaned_data['administration_entity'],
            end_year=cleaned_data['end_year'].year if cleaned_data["end_year"] else None,
            teaching_campus_name=cleaned_data['teaching_campus'].name if cleaned_data["teaching_campus"] else None,
            teaching_campus_organization_name=cleaned_data['teaching_campus'].organization.name
            if cleaned_data["teaching_campus"] else None,
            enrollment_campus_name=cleaned_data['enrollment_campus'].name
            if cleaned_data["enrollment_campus"] else None,
            enrollment_campus_organization_name=cleaned_data['enrollment_campus'].organization.name
            if cleaned_data["enrollment_campus"] else None,
            other_campus_activities=cleaned_data['other_campus_activities'],
            can_be_funded=cleaned_data['can_be_funded'],
            funding_orientation=cleaned_data['funding_direction'],
            can_be_international_funded=cleaned_data['can_be_international_funded'],
            international_funding_orientation=cleaned_data['international_funding_orientation'],
            ares_code=cleaned_data['ares_code'],
            ares_graca=cleaned_data['ares_graca'],
            ares_authorization=cleaned_data['ares_authorization'],
            code_inter_cfb=cleaned_data['code_inter_cfb'],
            coefficient=cleaned_data['coefficient'],
            duration_unit=cleaned_data['duration_unit'],
            leads_to_diploma=cleaned_data['leads_to_diploma'],
            printing_title=cleaned_data['diploma_printing_title'],
            professional_title=cleaned_data['professional_title'],
            aims=[
                (aim.code, aim.section) for aim in (cleaned_data['certificate_aims'] or [])
            ],
            constraint_type=cleaned_data['constraint_type'],
            min_constraint=cleaned_data['min_constraint'],
            max_constraint=cleaned_data['max_constraint'],
            remark_fr=cleaned_data['remark_fr'],
            remark_en=cleaned_data['remark_english'],
            organization_name=cleaned_data['teaching_campus'].organization.name
            if cleaned_data["teaching_campus"] else None,
            schedule_type=cleaned_data["schedule_type"],
        )

    def _convert_form_to_delete_trainings_command(
            self,
            training_form: training_forms.UpdateTrainingForm
    ) -> command_program_management.DeleteTrainingWithProgramTreeCommand:
        cleaned_data = training_form.cleaned_data
        return command_program_management.DeleteTrainingWithProgramTreeCommand(
            code=cleaned_data["code"],
            offer_acronym=cleaned_data["acronym"],
            version_name='',
            is_transition=False,
            from_year=cleaned_data["end_year"].year+1
        )
