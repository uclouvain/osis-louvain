import functools
from typing import Dict, List, Union

from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models import entity_version
from base.utils import operator
from base.utils.urls import reverse_with_get
from base.views.common import check_formations_impacted_by_update
from base.views.common import display_error_messages, display_warning_messages
from base.views.common import display_success_messages
from education_group.ddd import command as command_education_group
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception as exception_education_group
from education_group.ddd.domain.exception import TrainingNotFoundException, GroupNotFoundException
from education_group.ddd.service.read import get_training_service, get_group_service
from education_group.models.group_year import GroupYear
from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.command import UpdateTrainingVersionCommand
from program_management.ddd.domain import program_tree_version, exception as program_exception
from program_management.ddd.domain.program_tree_version import version_label
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.service.read import get_program_tree_version_from_node_service
from program_management.ddd.service.write import update_and_postpone_training_version_service
from program_management.forms import version, transition


class TrainingVersionUpdateView(PermissionRequiredMixin, View):
    permission_required = 'program_management.change_training_version'
    raise_exception = True

    template_name = "tree_version/training/update.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_program_tree_version_obj().is_official_standard:
            redirect_url = reverse('training_update', kwargs={
                'year': self.get_group_obj().year,
                'code': self.get_group_obj().code,
                'title': self.get_training_obj().acronym
            })
            return HttpResponseRedirect(redirect_url)
        return super().dispatch(request, *args, **kwargs)

    @transaction.non_atomic_requests
    def get(self, request, *args, **kwargs):
        version = self.get_program_tree_version_obj()
        context = {
            "training_version_form": self.training_version_form,
            "training_obj": self.get_training_obj(),
            "training_version_obj": version,
            "group_obj": self.get_group_obj(),
            "tabs": self.get_tabs(),
            "cancel_url": self.get_cancel_url(),
            "is_finality_types": self.get_training_obj().is_finality(),
            "version_suffix": (
                "-{}" if version.entity_id.is_specific_transition else "{}"
            ).format(version.transition_name),
            "version_label": version_label(version.entity_id)
        }
        return render(request, self.template_name, context)

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):
        if self.training_version_form.is_valid():
            version_identities = self.update_training_version()
            if not self.training_version_form.errors:
                self.display_success_messages(version_identities)
                self.display_delete_messages(version_identities)
                check_formations_impacted_by_update(self.get_group_obj().code,
                                                    self.get_group_obj().year,
                                                    request, self.get_group_obj().type)
                return HttpResponseRedirect(self.get_success_url())
        display_error_messages(self.request, self._get_default_error_messages())
        return self.get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        get_data = {'path': self.request.GET['path_to']} if self.request.GET.get('path_to') else {}
        return reverse_with_get(
            'element_identification',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get=get_data
        )

    def display_success_messages(self, identities: List['ProgramTreeVersionIdentity']) -> None:
        success_messages = []
        for identity in identities:
            success_messages.append(
                _(
                    "Training "
                    "<a href='%(link)s'> %(offer_acronym)s[%(acronym)s] (%(academic_year)s) </a> successfully updated."
                ) % {
                    "link": self.get_url_program_version(identity),
                    "offer_acronym": identity.offer_acronym,
                    "acronym": version_label(identity, only_label=True),
                    "academic_year": display_as_academic_year(identity.year)
                }
            )
        display_success_messages(self.request, success_messages, extra_tags='safe')

    def display_delete_messages(self, version_identities: List['ProgramTreeVersionIdentity']):

        is_new_end_year_lower_than_initial_one = operator.is_year_lower(
            self.training_version_form.cleaned_data["end_year"],
            self.training_version_form.initial['end_year']
        )
        if is_new_end_year_lower_than_initial_one:
            last_identity = version_identities[-1]
            delete_message = _(
                "Training %(offer_acronym)s[%(acronym)s] successfully deleted from %(academic_year)s."
            ) % {
                "offer_acronym": last_identity.offer_acronym,
                "acronym": version_label(last_identity, only_label=True),
                "academic_year": display_as_academic_year(self.training_version_form.cleaned_data["end_year"] + 1)
            }
            display_success_messages(self.request, delete_message, extra_tags='safe')

    def get_url_program_version(self, version_id: 'ProgramTreeVersionIdentity') -> str:
        node_identity = NodeIdentitySearch().get_from_tree_version_identity(version_id)
        return reverse(
            "element_identification",
            kwargs={
                'year': node_identity.year,
                'code': node_identity.code,
            }
        )

    def get_cancel_url(self) -> str:
        return self.get_success_url()

    def update_training_version(self) -> List['ProgramTreeVersionIdentity']:
        try:
            update_command = self._convert_form_to_update_training_version_command(self.training_version_form)
            return update_and_postpone_training_version_service.update_and_postpone_training_version(update_command)
        except MultipleBusinessExceptions as multiple_exceptions:
            for e in multiple_exceptions.exceptions:
                if isinstance(e, program_exception.FinalitiesEndDateGreaterThanTheirMasters2MException) or \
                        isinstance(e, program_exception.Program2MEndDateLowerThanItsFinalitiesException):
                    self.training_version_form.add_error('end_year', e.message)
                elif isinstance(e, exception_education_group.ContentConstraintTypeMissing):
                    self.training_version_form.add_error("constraint_type", e.message)
                elif isinstance(e, exception_education_group.ContentConstraintMinimumMaximumMissing) or \
                        isinstance(
                            e,
                            exception_education_group.ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum
                        ):
                    self.training_version_form.add_error("min_constraint", e.message)
                    self.training_version_form.add_error("max_constraint", "")
                elif isinstance(e, exception_education_group.ContentConstraintMinimumInvalid):
                    self.training_version_form.add_error("min_constraint", e.message)
                elif isinstance(e, exception_education_group.ContentConstraintMaximumInvalid):
                    self.training_version_form.add_error("max_constraint", e.message)
                else:
                    self.training_version_form.add_error(None, e.message)
        except exception_education_group.GroupCopyConsistencyException as e:
            display_warning_messages(self.request, e.message)
            return [
                program_tree_version.ProgramTreeVersionIdentity(
                    offer_acronym=update_command.offer_acronym,
                    year=year,
                    version_name=update_command.version_name,
                    transition_name=update_command.transition_name
                ) for year in range(update_command.year, e.conflicted_fields_year)
            ]
        except program_exception.CannotDeleteSpecificVersionDueToTransitionVersionEndDate as e:
            self.training_version_form.add_error('end_year', "")
            self.training_version_form.add_error(
                None, _("Impossible to put end date to %(end_year)s: %(msg)s") % {
                    "msg": e.message,
                    "end_year": display_as_academic_year(update_command.end_year)
                }
            )
        return []

    @cached_property
    def training_version_form(self) \
            -> Union['version.UpdateTrainingVersionForm', 'transition.UpdateTrainingTransitionVersionForm']:
        training_version_identity = self.get_program_tree_version_obj().entity_id
        form_parameters = self._get_form_parameters(training_version_identity)
        if training_version_identity.is_transition:
            return transition.UpdateTrainingTransitionVersionForm(**form_parameters)
        return version.UpdateTrainingVersionForm(**form_parameters)

    def _get_form_parameters(self, training_version_identity):
        return {
            'data': self.request.POST or None,
            'user': self.request.user,
            'year': self.kwargs['year'],
            'training_version_identity': training_version_identity,
            'training_type': self.get_training_obj().type,
            'initial': self._get_training_version_form_initial_values()
        }

    @functools.lru_cache()
    def get_training_obj(self) -> 'Training':
        try:
            training_acronym = self.get_program_tree_version_obj().entity_id.offer_acronym
            get_cmd = command_education_group.GetTrainingCommand(
                acronym=training_acronym,
                year=self.kwargs['year']
            )
            return get_training_service.get_training(get_cmd)
        except TrainingNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command_education_group.GetGroupCommand(
                code=self.kwargs["code"],
                year=self.kwargs["year"]
            )
            return get_group_service.get_group(get_cmd)
        except GroupNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_program_tree_version_obj(self) -> 'ProgramTreeVersion':
        get_cmd = command.GetProgramTreeVersionFromNodeCommand(
            code=self.kwargs['code'],
            year=self.kwargs['year']
        )
        return get_program_tree_version_from_node_service.get_program_tree_version_from_node(get_cmd)

    @functools.lru_cache()
    def get_program_tree_obj(self) -> 'ProgramTree':
        return self.get_program_tree_version_obj().get_tree()

    def get_permission_object(self):
        return GroupYear.objects.select_related('management_entity').get(
            partial_acronym=self.kwargs['code'],
            academic_year__year=self.kwargs['year']
        )

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "tree_version/training/blocks/identification.html"
            },
            {
                "text": _("Diplomas /  Certificates"),
                "active": False,
                "display": True,
                "include_html": "tree_version/training/blocks/diplomas_certificates.html"
            },
        ]

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_training_version_form_initial_values(self) -> Dict:
        training_version = self.get_program_tree_version_obj()
        training_obj = self.get_training_obj()
        group_obj = self.get_group_obj()
        administration_entity_obj = entity_version.find(training_obj.administration_entity.acronym)

        form_initial_values = {
            'transition_name': training_version.transition_name,
            'version_name': training_version.version_name,
            'version_title_fr': training_version.title_fr,
            'version_title_en': training_version.title_en,
            'end_year': training_version.end_year_of_existence,

            "code": group_obj.code,
            "active": training_obj.status.value,
            "schedule_type": training_obj.schedule_type.value,
            "credits": group_obj.credits,
            "constraint_type": group_obj.content_constraint.type.name
            if group_obj.content_constraint.type else None,
            "min_constraint": group_obj.content_constraint.minimum,
            "max_constraint": group_obj.content_constraint.maximum,
            "offer_title_fr": training_obj.titles.title_fr,
            "offer_title_en": training_obj.titles.title_en,
            "offer_partial_title_fr": training_obj.titles.partial_title_fr,
            "offer_partial_title_en": training_obj.titles.partial_title_en,
            "keywords": training_obj.keywords,
            "academic_type": training_obj.academic_type.value,
            "duration": training_obj.duration,
            "category": _("Training"),
            "type": training_obj.type.value,
            "duration_unit": training_obj.duration_unit.value if training_obj.duration_unit else None,
            "internship_presence": training_obj.internship_presence.value if training_obj.internship_presence else None,
            "is_enrollment_enabled": training_obj.is_enrollment_enabled,
            "has_online_re_registration": training_obj.has_online_re_registration,
            "has_partial_deliberation": training_obj.has_partial_deliberation,
            "has_admission_exam": training_obj.has_admission_exam,
            "has_dissertation": training_obj.has_dissertation,
            "produce_university_certificate": training_obj.produce_university_certificate,
            "decree_category": training_obj.decree_category.value if training_obj.decree_category else None,
            "rate_code": training_obj.rate_code.value if training_obj.rate_code else None,
            "main_language": training_obj.main_language.name,
            "english_activities": training_obj.english_activities.value if training_obj.english_activities else None,
            "other_language_activities": training_obj.other_language_activities.value
            if training_obj.other_language_activities else None,
            "main_domain": "{} - {} {}".format(training_obj.main_domain.decree_name,
                                               training_obj.main_domain.code,
                                               training_obj.main_domain.name)
            if training_obj.main_domain else None,
            "secondary_domains": ", ".join(str(dom) for dom in (training_obj.secondary_domains or [])),
            "isced_domain": str(training_obj.isced_domain) if training_obj.isced_domain else None,
            "internal_comment": training_obj.internal_comment,

            "management_entity": group_obj.management_entity.acronym,
            "administration_entity": "{} - {}".format(
                administration_entity_obj.acronym, administration_entity_obj.title
            ) if administration_entity_obj else None,
            "academic_year": training_obj.academic_year,
            "start_year": display_as_academic_year(group_obj.start_year),
            "teaching_campus": group_obj.teaching_campus.name,
            "enrollment_campus": "{} - {}".format(training_obj.enrollment_campus.name,
                                                  training_obj.enrollment_campus.university_name),
            "other_campus_activities": training_obj.other_campus_activities.value
            if training_obj.other_campus_activities else None,

            "can_be_funded": training_obj.funding.can_be_funded,
            "funding_direction": training_obj.funding.funding_orientation.value
            if training_obj.funding.funding_orientation else None,
            "can_be_international_funded": training_obj.funding.can_be_international_funded,
            "international_funding_orientation": training_obj.funding.international_funding_orientation.value
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

    def _convert_form_to_update_training_version_command(
            self, form: 'version.UpdateTrainingVersionForm'
    ) -> UpdateTrainingVersionCommand:
        return UpdateTrainingVersionCommand(
            offer_acronym=self.get_program_tree_version_obj().entity_id.offer_acronym,
            version_name=self.get_program_tree_version_obj().entity_id.version_name,
            year=self.get_program_tree_version_obj().entity_id.year,
            transition_name=self.get_program_tree_version_obj().entity_id.transition_name,

            title_en=form.cleaned_data["version_title_en"],
            title_fr=form.cleaned_data["version_title_fr"],
            end_year=form.cleaned_data["end_year"],
            management_entity_acronym=form.cleaned_data['management_entity'],
            teaching_campus_name=form.cleaned_data['teaching_campus'].name if form.cleaned_data["teaching_campus"]
            else None,
            teaching_campus_organization_name=form.cleaned_data['teaching_campus'].organization.name
            if form.cleaned_data["teaching_campus"] else None,
            credits=form.cleaned_data['credits'],
            constraint_type=form.cleaned_data['constraint_type'],
            min_constraint=form.cleaned_data['min_constraint'],
            max_constraint=form.cleaned_data['max_constraint'],
            remark_fr=form.cleaned_data['remark_fr'],
            remark_en=form.cleaned_data['remark_english'],
        )
