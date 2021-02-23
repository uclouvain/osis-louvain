##############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import functools
from collections import OrderedDict

from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from base import models as mdl
from base.business.education_group import has_coorganization
from base.business.education_groups import general_information_sections
from base.models import academic_year
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.utils.urls import reverse_with_get
from base.views.common import display_warning_messages
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain.service.identity_search import TrainingIdentitySearch
from education_group.ddd.service.read import get_group_service, get_training_service
from education_group.forms.academic_year_choices import get_academic_year_choices
from education_group.forms.tree_version_choices import get_tree_versions_choices
from education_group.views.mixin import ElementSelectedClipBoardMixin
from education_group.views.proxy import read
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.command import GetLastExistingTransitionVersionNameCommand
from program_management.ddd.domain.node import NodeIdentity, NodeNotFoundException
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.read import node_identity_service, get_last_existing_transition_version_service
from program_management.forms.custom_xls import CustomXlsForm
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element

Tab = read.Tab  # FIXME :: fix imports (and remove this line)


class TrainingRead(PermissionRequiredMixin, ElementSelectedClipBoardMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    active_tab = None

    @cached_property
    def path(self):
        path = self.request.GET.get('path')
        if path is None:
            root_element = Element.objects.get(
                group_year__academic_year__year=self.kwargs['year'],
                group_year__partial_acronym=self.kwargs['code'].upper()
            )
            path = str(root_element.pk)
        return path

    @cached_property
    def is_root_node(self):
        node_identity = node_identity_service.get_node_identity_from_element_id(
            command_program_management.GetNodeIdentityFromElementId(element_id=self.get_root_id())
        )
        return node_identity == self.node_identity

    @cached_property
    def has_transition_version(self) -> 'bool':
        cmd = GetLastExistingTransitionVersionNameCommand(
            version_name=self.program_tree_version_identity.version_name,
            offer_acronym=self.program_tree_version_identity.offer_acronym,
            transition_name=self.program_tree_version_identity.transition_name,
            year=self.program_tree_version_identity.year
        )
        return bool(get_last_existing_transition_version_service.get_last_existing_transition_version_identity(cmd))

    @cached_property
    def node_identity(self) -> 'NodeIdentity':
        return NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])

    @cached_property
    def training_identity(self) -> 'TrainingIdentity':
        return TrainingIdentitySearch().get_from_program_tree_version_identity(self.program_tree_version_identity)

    @cached_property
    def program_tree_version_identity(self) -> 'ProgramTreeVersionIdentity':
        return ProgramTreeVersionIdentitySearch().get_from_node_identity(self.node_identity)

    @cached_property
    def current_version(self) -> 'ProgramTreeVersion':
        return ProgramTreeVersionRepository.get(self.program_tree_version_identity)

    @cached_property
    def education_group_version(self) -> 'EducationGroupVersion':
        try:
            return EducationGroupVersion.objects.select_related(
                'offer', 'root_group__academic_year', 'root_group__education_group_type'
            ).get(
                root_group__partial_acronym=self.kwargs["code"],
                root_group__academic_year__year=self.kwargs["year"]
            )
        except (EducationGroupVersion.DoesNotExist, Element.DoesNotExist):
            raise Http404

    @cached_property
    def group(self) -> 'Group':
        get_group_cmd = command.GetGroupCommand(year=self.kwargs['year'], code=self.kwargs['code'])
        return get_group_service.get_group(get_group_cmd)

    @cached_property
    def training(self) -> 'Training':
        get_training_cmd = command.GetTrainingCommand(
            year=self.kwargs['year'],
            acronym=self.training_identity.acronym
        )
        return get_training_service.get_training(get_training_cmd)

    def get_root_id(self) -> int:
        return int(self.path.split("|")[0])

    @cached_property
    def get_object(self) -> 'Node':
        try:
            return self.get_tree().get_node(self.path)
        except NodeNotFoundException:
            root_node = self.get_tree().root_node
            version_identity = self.program_tree_version_identity
            message = _(
                "The formation you work with doesn't exist (or is not at the same position) "
                "in the tree {root.title}{version} in {root.year}."
                "You've been redirected to the root {root.code} ({root.year})"
            ).format(
                root=root_node,
                version="[{}]".format(version_identity.version_name)
                if version_identity and not version_identity.is_official_standard else ""
            )
            display_warning_messages(self.request, message)
            return root_node

    def get_context_data(self, **kwargs):
        user_person = self.request.user.person
        return {
            **super().get_context_data(**kwargs),
            "person": user_person,
            "enums": mdl.enums.education_group_categories,
            "tab_urls": self.get_tab_urls(),
            "group": self.group,
            "training": self.training,  # TODO: Rename to training (DDD concept)
            "node_path": self.path,
            "form_xls_custom": CustomXlsForm(year=self.node_identity.year, code=self.node_identity.code),
            "academic_year_choices": get_academic_year_choices(
                self.node_identity,
                self.path,
                _get_view_name_from_tab(self.active_tab),
            ) if self.is_root_node else None,
            "selected_element_clipboard": self.get_selected_element_clipboard_message(),
            "current_version": self.current_version,
            "versions_choices": get_tree_versions_choices(self.node_identity, _get_view_name_from_tab(self.active_tab)),
            "is_root_node": self.is_root_node,
            # TODO: Two lines below to remove when finished reorganized templates
            "education_group_version": self.education_group_version,
            "group_year": self.education_group_version.root_group,
            "tree_json_url": self.get_tree_json_url(),
            "tree_root_id": self.get_root_id(),
            "create_group_url": self.get_create_group_url(),
            "create_training_url": self.get_create_training_url(),
            "create_mini_training_url": self.get_create_mini_training_url(),
            "update_training_url": self.get_update_training_url(),
            "update_permission_name": self.get_update_permission_name(),
            "delete_permanently_training_url": self.get_delete_permanently_training_url(),
            "delete_permanently_tree_version_url": self.get_delete_permanently_tree_version_url(),
            "delete_permanently_tree_version_permission_name":
                self.get_delete_permanently_tree_version_permission_name(),
            "create_specific_version_url": self.get_create_specific_version_url(),
            "create_transition_version_url": self.get_create_transition_version_url(),
            "create_version_permission_name": self.get_create_version_permission_name(),
            "xls_ue_prerequisites": reverse("education_group_learning_units_prerequisites",
                                            args=[self.education_group_version.root_group.academic_year.year,
                                                  self.education_group_version.root_group.partial_acronym]
                                            ),
            "xls_ue_is_prerequisite": reverse("education_group_learning_units_is_prerequisite_for",
                                              args=[self.education_group_version.root_group.academic_year.year,
                                                    self.education_group_version.root_group.partial_acronym]
                                              ),
            "generate_pdf_url": reverse("group_pdf_content",
                                        args=[self.education_group_version.root_group.academic_year.year,
                                              self.education_group_version.root_group.partial_acronym,
                                              ]
                                        ),
            "show_coorganization": has_coorganization(self.education_group_version.offer),
            "view_publish_btn":
                self.request.user.has_perm('base.view_publish_btn') and
                (self.have_general_information_tab() or self.have_admission_condition_tab() or
                 self.have_skills_and_achievements_tab()),
            "publish_url": self.get_publish_url(),

        }

    def get_permission_object(self) -> 'GroupYear':
        return self.education_group_version.root_group

    def get_create_group_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.GROUP.name}) + \
               "?path_to={}".format(self.path)

    def get_create_mini_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.MINI_TRAINING.name}) + \
               "?path_to={}".format(self.path)

    def get_create_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.TRAINING.name}) + \
               "?path_to={}".format(self.path)

    def get_update_training_url(self):
        if self.current_version.is_official_standard:
            return reverse_with_get(
                'training_update',
                kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year'],
                        'title': self.training_identity.acronym},
                get={"path_to": self.path, "tab": self.active_tab.name}
            )
        return reverse_with_get(
            'training_version_update',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get={"path_to": self.path, "tab": self.active_tab.name}
        )

    def get_update_permission_name(self) -> str:
        if self.current_version.is_official_standard:
            return "base.change_training"
        return "program_management.change_training_version"

    def get_delete_permanently_training_url(self):
        if self.program_tree_version_identity.is_official_standard:
            return reverse(
                'training_delete',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}
            )

    def get_delete_permanently_tree_version_url(self):
        if not self.program_tree_version_identity.is_official_standard:
            return reverse(
                'delete_permanently_tree_version',
                kwargs={
                    'year': self.node_identity.year,
                    'code': self.node_identity.code,
                }
            )

    def get_delete_permanently_tree_version_permission_name(self):
        return "program_management.delete_permanently_training_version"

    def get_create_specific_version_url(self):
        if self.is_root_node and self.program_tree_version_identity.is_official_standard:
            return reverse(
                'create_education_group_specific_version',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}
            ) + "?path={}".format(self.path)

    def get_create_transition_version_url(self):
        if self.is_root_node and \
                not self.program_tree_version_identity.is_transition and \
                not self.has_transition_version:
            return reverse(
                'create_education_group_transition_version',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}
            ) + "?path={}".format(self.path)

    def get_tree_json_url(self) -> str:
        return reverse_with_get(
            'tree_json',
            kwargs={'root_id': self.get_root_id()},
            get={"path": self.path}
        )

    def get_create_version_permission_name(self) -> str:
        return "base.add_training_version"

    def get_tab_urls(self):
        tab_urls = OrderedDict({
            Tab.IDENTIFICATION: {
                'text': _('Identification'),
                'active': Tab.IDENTIFICATION == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.IDENTIFICATION, self.node_identity, self.path),
            },
            Tab.DIPLOMAS_CERTIFICATES: {
                'text': _('Diplomas /  Certificates'),
                'active': Tab.DIPLOMAS_CERTIFICATES == self.active_tab,
                'display': self.current_version.is_official_standard,
                'url': get_tab_urls(Tab.DIPLOMAS_CERTIFICATES, self.node_identity, self.path),
            },
            Tab.ADMINISTRATIVE_DATA: {
                'text': _('Administrative data'),
                'active': Tab.ADMINISTRATIVE_DATA == self.active_tab,
                'display': self.have_administrative_data_tab(),
                'url': get_tab_urls(Tab.ADMINISTRATIVE_DATA, self.node_identity, self.path),
            },
            Tab.CONTENT: {
                'text': _('Content'),
                'active': Tab.CONTENT == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.CONTENT, self.node_identity, self.path),
            },
            Tab.UTILIZATION: {
                'text': _('Utilizations'),
                'active': Tab.UTILIZATION == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.UTILIZATION, self.node_identity, self.path),
            },
            Tab.GENERAL_INFO: {
                'text': _('General informations'),
                'active': Tab.GENERAL_INFO == self.active_tab,
                'display': self.have_general_information_tab(),
                'url': get_tab_urls(Tab.GENERAL_INFO, self.node_identity, self.path),
            },
            Tab.SKILLS_ACHIEVEMENTS: {
                'text': capfirst(_('skills and achievements')),
                'active': Tab.SKILLS_ACHIEVEMENTS == self.active_tab,
                'display': self.have_skills_and_achievements_tab(),
                'url': get_tab_urls(Tab.SKILLS_ACHIEVEMENTS, self.node_identity, self.path),
            },
            Tab.ADMISSION_CONDITION: {
                'text': _('Conditions'),
                'active': Tab.ADMISSION_CONDITION == self.active_tab,
                'display': self.have_admission_condition_tab(),
                'url': get_tab_urls(Tab.ADMISSION_CONDITION, self.node_identity, self.path),
            },
        })

        return read.validate_active_tab(tab_urls)

    @functools.lru_cache()
    def get_current_academic_year(self):
        return academic_year.starting_academic_year()

    def have_administrative_data_tab(self):
        return self.group.type not in TrainingType.root_master_2m_types_enum() and \
               self.current_version.is_official_standard

    def have_general_information_tab(self):
        return self.current_version.is_official_standard and \
               self.group.type.name in general_information_sections.SECTIONS_PER_OFFER_TYPE

    def have_skills_and_achievements_tab(self):
        return self.current_version.is_official_standard and \
               self.group.type.name in TrainingType.with_skills_achievements()

    def have_admission_condition_tab(self):
        return self.current_version.is_official_standard and \
               self.group.type.name in TrainingType.with_admission_condition()

    def get_publish_url(self):
        return reverse('publish_general_information', args=[
            self.node_identity.year,
            self.node_identity.code
        ]) + "?path={}".format(self.path)


def _get_view_name_from_tab(tab: Tab):
    return {
        Tab.IDENTIFICATION: 'training_identification',
        Tab.DIPLOMAS_CERTIFICATES: 'training_diplomas',
        Tab.ADMINISTRATIVE_DATA: 'training_administrative_data',
        Tab.CONTENT: 'training_content',
        Tab.UTILIZATION: 'training_utilization',
        Tab.GENERAL_INFO: 'training_general_information',
        Tab.SKILLS_ACHIEVEMENTS: 'training_skills_achievements',
        Tab.ADMISSION_CONDITION: 'training_admission_condition',
    }[tab]


def get_tab_urls(tab: Tab, node_identity: 'NodeIdentity', path: 'Path' = None) -> str:
    path = path or ""
    url_parameters = \
        "?path={}&tab={}#achievement_".format(path, tab) if tab == Tab.SKILLS_ACHIEVEMENTS else "?path={}".format(path)

    return reverse(
        _get_view_name_from_tab(tab),
        args=[node_identity.year, node_identity.code]
    ) + url_parameters
