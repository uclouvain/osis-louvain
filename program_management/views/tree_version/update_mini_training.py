import functools
from typing import Dict, List

from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils import operator
from base.utils.urls import reverse_with_get
from base.views.common import display_error_messages, display_warning_messages, display_success_messages
from education_group.ddd import command as command_education_group
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception as exception_education_group
from education_group.ddd.domain.exception import GroupNotFoundException, \
    MiniTrainingNotFoundException
from education_group.ddd.service.read import get_group_service, get_mini_training_service
from education_group.models.group_year import GroupYear
from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.command import UpdateMiniTrainingVersionCommand
from program_management.ddd.domain import program_tree_version
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.service.read import get_program_tree_version_from_node_service
from program_management.ddd.service.write import update_and_postpone_mini_training_version_service
from program_management.forms import version
from base.views.common import check_formations_impacted_by_update


class MiniTrainingVersionUpdateView(PermissionRequiredMixin, View):
    permission_required = 'program_management.change_minitraining_version'
    raise_exception = True

    template_name = "tree_version/mini_training/update.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_program_tree_version_obj().is_official_standard:
            redirect_url = reverse('mini_training_update', kwargs={
                'year': self.get_group_obj().year,
                'code': self.get_group_obj().code,
                'acronym': self.get_mini_training_obj().acronym
            })
            return HttpResponseRedirect(redirect_url)
        return super().dispatch(request, *args, **kwargs)

    @transaction.non_atomic_requests
    def get(self, request, *args, **kwargs):
        context = {
            "mini_training_version_form": self.mini_training_version_form,
            "mini_training_obj": self.get_mini_training_obj(),
            "mini_training_version_obj": self.get_program_tree_version_obj(),
            "group_obj": self.get_group_obj(),
            "tabs": self.get_tabs(),
            "cancel_url": self.get_cancel_url()
        }
        return render(request, self.template_name, context)

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):
        if self.mini_training_version_form.is_valid():
            version_identities = self.update_mini_training_version()
            if not self.mini_training_version_form.errors:
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
                    "Mini-Training "
                    "<a href='%(link)s'> %(offer_acronym)s[%(acronym)s] (%(academic_year)s) </a> successfully updated."
                ) % {
                    "link": self.get_url_program_version(identity),
                    "offer_acronym": identity.offer_acronym,
                    "acronym": identity.version_name,
                    "academic_year": display_as_academic_year(identity.year)
                }
            )
        display_success_messages(self.request, success_messages, extra_tags='safe')

    def display_delete_messages(self, version_identities: List['ProgramTreeVersionIdentity']):
        last_identity = version_identities[-1]
        is_new_end_year_lower_than_initial_one = operator.is_year_lower(
            self.mini_training_version_form.cleaned_data["end_year"],
            self.mini_training_version_form.initial['end_year']
        )
        if is_new_end_year_lower_than_initial_one:
            delete_message = _(
                "Mini-Training %(offer_acronym)s[%(acronym)s] successfully deleted from %(academic_year)s."
            ) % {
                "offer_acronym": last_identity.offer_acronym,
                "acronym": last_identity.version_name,
                "academic_year": display_as_academic_year(self.mini_training_version_form.cleaned_data["end_year"] + 1)
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

    def update_mini_training_version(self) -> List['ProgramTreeVersionIdentity']:
        try:
            update_command = self._convert_form_to_update_mini_training_version_command(self.mini_training_version_form)
            return update_and_postpone_mini_training_version_service.update_and_postpone_mini_training_version(
                update_command
            )
        except exception_education_group.ContentConstraintTypeMissing as e:
            self.mini_training_version_form.add_error("constraint_type", e.message)
        except (exception_education_group.ContentConstraintMinimumMaximumMissing,
                exception_education_group.ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum) as e:
            self.mini_training_version_form.add_error("min_constraint", e.message)
            self.mini_training_version_form.add_error("max_constraint", "")
        except MultipleBusinessExceptions as multiple_exceptions:
            for e in multiple_exceptions.exceptions:
                if isinstance(e, exception_education_group.ContentConstraintTypeMissing):
                    self.mini_training_version_form.add_error("constraint_type", e.message)
                elif isinstance(e, exception_education_group.ContentConstraintMinimumMaximumMissing) or \
                        isinstance(
                            e,
                            exception_education_group.ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum
                        ):
                    self.mini_training_version_form.add_error("min_constraint", e.message)
                    self.mini_training_version_form.add_error("max_constraint", "")
                elif isinstance(e, exception_education_group.ContentConstraintMinimumInvalid):
                    self.mini_training_version_form.add_error("min_constraint", e.message)
                elif isinstance(e, exception_education_group.ContentConstraintMaximumInvalid):
                    self.mini_training_version_form.add_error("max_constraint", e.message)
                else:
                    self.mini_training_version_form.add_error(None, e.message)
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
        return []

    @cached_property
    def mini_training_version_form(self) -> 'version.UpdateMiniTrainingVersionForm':
        mini_training_version_identity = self.get_program_tree_version_obj().entity_id
        return version.UpdateMiniTrainingVersionForm(
            data=self.request.POST or None,
            user=self.request.user,
            year=self.kwargs['year'],
            mini_training_version_identity=mini_training_version_identity,
            mini_training_type=self.get_mini_training_obj().type,
            initial=self._get_mini_training_version_form_initial_values()
        )

    @functools.lru_cache()
    def get_mini_training_obj(self) -> 'MiniTraining':
        try:
            mini_training_abbreviated_title = self.get_program_tree_version_obj().entity_id.offer_acronym
            get_cmd = command_education_group.GetMiniTrainingCommand(
                acronym=mini_training_abbreviated_title,
                year=self.kwargs['year']
            )
            return get_mini_training_service.get_mini_training(get_cmd)
        except MiniTrainingNotFoundException:
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
                "include_html": "tree_version/mini_training/blocks/identification.html"
            },
        ]

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_mini_training_version_form_initial_values(self) -> Dict:
        mini_training_version = self.get_program_tree_version_obj()
        mini_training_obj = self.get_mini_training_obj()
        group_obj = self.get_group_obj()

        form_initial_values = {
            'version_name': mini_training_version.version_name,
            'version_title_fr': mini_training_version.title_fr,
            'version_title_en': mini_training_version.title_en,
            'end_year': mini_training_version.end_year_of_existence,

            "category": _("Mini-Training"),
            "type": mini_training_obj.type.value,
            "offer_title_fr": mini_training_obj.titles.title_fr,
            "offer_title_en": mini_training_obj.titles.title_en,
            "academic_year": mini_training_obj.academic_year,
            "code": group_obj.code,
            "status": mini_training_obj.status.value,
            "schedule_type": mini_training_obj.schedule_type.value,
            "credits": group_obj.credits,
            "constraint_type": group_obj.content_constraint.type.name
            if group_obj.content_constraint.type else None,
            "min_constraint": group_obj.content_constraint.minimum,
            "max_constraint": group_obj.content_constraint.maximum,
            "keywords": mini_training_obj.keywords,
            "remark_fr": group_obj.remark.text_fr,
            "remark_en": group_obj.remark.text_en,
            "management_entity": group_obj.management_entity.acronym,
            "start_year": display_as_academic_year(group_obj.start_year),
            "teaching_campus": group_obj.teaching_campus.name,
        }
        return form_initial_values

    def _convert_form_to_update_mini_training_version_command(
            self, form: 'version.UpdateMiniTrainingVersionForm'
    ) -> UpdateMiniTrainingVersionCommand:
        return UpdateMiniTrainingVersionCommand(
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
            remark_en=form.cleaned_data['remark_en'],
        )
