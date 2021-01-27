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
from base.business.education_groups import general_information_sections
from base.models import academic_year
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import MiniTrainingType
from base.utils.urls import reverse_with_get
from base.views.common import display_warning_messages
from education_group.ddd import command
from education_group.ddd.domain.service.identity_search import MiniTrainingIdentitySearch
from education_group.ddd.service.read import get_group_service, get_mini_training_service
from education_group.forms.academic_year_choices import get_academic_year_choices
from education_group.forms.tree_version_choices import get_tree_versions_choices
from education_group.views.mixin import ElementSelectedClipBoardMixin
from education_group.views.proxy import read
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.domain.node import NodeIdentity, NodeNotFoundException
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.read import node_identity_service
from program_management.forms.custom_xls import CustomXlsForm
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element

Tab = read.Tab  # FIXME :: fix imports (and remove this line)


class MiniTrainingRead(PermissionRequiredMixin, ElementSelectedClipBoardMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    active_tab = None

    @functools.lru_cache()
    def get_path(self):
        path = self.request.GET.get('path')
        if path is None:
            root_element = Element.objects.get(
                group_year__academic_year__year=self.kwargs['year'],
                group_year__partial_acronym=self.kwargs['code']
            )
            path = str(root_element.pk)
        return path

    @functools.lru_cache()
    def is_root_node(self):
        node_identity = node_identity_service.get_node_identity_from_element_id(
            command_program_management.GetNodeIdentityFromElementId(element_id=self.get_root_id())
        )
        return node_identity == self.node_identity

    @cached_property
    def node_identity(self) -> 'NodeIdentity':
        return NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])

    @cached_property
    def program_tree_version_identity(self) -> 'ProgramTreeVersionIdentity':
        return ProgramTreeVersionIdentitySearch().get_from_node_identity(self.node_identity)

    @cached_property
    def current_version(self) -> 'ProgramTreeVersion':
        return ProgramTreeVersionRepository.get(self.program_tree_version_identity)

    @functools.lru_cache()
    def get_current_academic_year(self):
        return academic_year.starting_academic_year()

    @functools.lru_cache()
    def get_education_group_version(self):
        try:
            return EducationGroupVersion.objects.select_related(
                'offer', 'root_group', 'root_group__academic_year'
            ).get(
                root_group__partial_acronym=self.kwargs["code"],
                root_group__academic_year__year=self.kwargs["year"]
            )
        except (EducationGroupVersion.DoesNotExist, Element.DoesNotExist):
            raise Http404

    @functools.lru_cache()
    def get_group(self) -> 'Group':
        get_group_cmd = command.GetGroupCommand(year=self.kwargs['year'], code=self.kwargs['code'])
        return get_group_service.get_group(get_group_cmd)

    @functools.lru_cache()
    def get_mini_training(self) -> 'MiniTraining':
        get_mini_training_cmd = command.GetMiniTrainingCommand(
            year=self.kwargs['year'],
            acronym=self.get_mini_training_identity().acronym
        )
        return get_mini_training_service.get_mini_training(get_mini_training_cmd)

    @functools.lru_cache()
    def get_object(self):
        try:
            return self.get_tree().get_node(self.get_path())
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
                if version_identity and not version_identity.is_standard() else ""
            )
            display_warning_messages(self.request, message)
            return root_node

    @functools.lru_cache()
    def get_mini_training_identity(self) -> 'MiniTrainingIdentity':
        return MiniTrainingIdentitySearch.get_from_group_identity(self.get_group().entity_identity)

    def get_root_id(self) -> int:
        return int(self.get_path().split("|")[0])

    def get_context_data(self, **kwargs):
        user_person = self.request.user.person
        return {
            **super().get_context_data(**kwargs),
            "person": user_person,
            "enums": mdl.enums.education_group_categories,
            "group": self.get_group(),
            "mini_training": self.get_mini_training(),
            "node_path": self.get_path(),
            "tab_urls": self.get_tab_urls(),
            "tree_json_url": self.get_tree_json_url(),
            "tree_root_id": self.get_root_id(),
            "form_xls_custom": CustomXlsForm(year=self.get_group().year, code=self.get_group().code),
            "education_group_version": self.get_education_group_version(),
            "academic_year_choices": get_academic_year_choices(
                self.node_identity,
                self.get_path(),
                _get_view_name_from_tab(self.active_tab),
            ) if self.is_root_node() else None,
            "selected_element_clipboard": self.get_selected_element_clipboard_message(),
            "current_version": self.current_version,
            "versions_choices": get_tree_versions_choices(self.node_identity, _get_view_name_from_tab(self.active_tab)),
            "xls_ue_prerequisites": reverse("education_group_learning_units_prerequisites",
                                            args=[self.get_education_group_version().root_group.academic_year.year,
                                                  self.get_education_group_version().root_group.partial_acronym]
                                            ),
            "xls_ue_is_prerequisite": reverse("education_group_learning_units_is_prerequisite_for",
                                              args=[self.get_education_group_version().root_group.academic_year.year,
                                                    self.get_education_group_version().root_group.partial_acronym]
                                              ),
            "generate_pdf_url": reverse("group_pdf_content",
                                        args=[self.get_education_group_version().root_group.academic_year.year,
                                              self.get_education_group_version().root_group.partial_acronym]
                                        ),
            # TODO: Remove when finished reorganized template
            "group_year": self.get_education_group_version().root_group,
            "create_group_url": self.get_create_group_url(),
            "create_training_url": self.get_create_training_url(),
            "create_mini_training_url": self.get_create_mini_training_url(),
            "update_mini_training_url": self.get_update_mini_training_url(),
            "update_permission_name": self.get_update_permission_name(),
            "delete_permanently_mini_training_url": self.get_delete_permanently_mini_training_url(),
            "delete_permanently_tree_version_url": self.get_delete_permanently_tree_version_url(),
            "delete_permanently_tree_version_permission_name":
                self.get_delete_permanently_tree_version_permission_name(),
            "create_version_url": self.get_create_version_url(),
            "create_version_permission_name": self.get_create_version_permission_name(),
            "is_root_node": self.is_root_node(),
            "view_publish_btn":
                self.request.user.has_perm('base.view_publish_btn') and
                (self.have_general_information_tab() or self.have_skills_and_achievements_tab()),
            "publish_url": self.get_publish_url()
        }

    def get_permission_object(self):
        return self.get_education_group_version().root_group

    def get_create_group_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.GROUP.name}) + \
               "?path_to={}".format(self.get_path())

    def get_create_mini_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.MINI_TRAINING.name}) + \
               "?path_to={}".format(self.get_path())

    def get_create_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.TRAINING.name}) + \
               "?path_to={}".format(self.get_path())

    def get_update_mini_training_url(self) -> str:
        if self.current_version.is_standard_version:
            return reverse_with_get(
                'mini_training_update',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code,
                        'acronym': self.get_mini_training_identity().acronym},
                get={"path": self.get_path(), "tab": self.active_tab.name}
            )
        return reverse_with_get(
            'mini_training_version_update',
            kwargs={'year': self.node_identity.year, 'code': self.node_identity.code},
            get={"path": self.get_path(), "tab": self.active_tab.name}
        )

    def get_tree_json_url(self) -> str:
        return reverse_with_get(
            'tree_json',
            kwargs={'root_id': self.get_root_id()},
            get={"path": self.get_path()}
        )

    def get_update_permission_name(self) -> str:
        if self.current_version.is_standard_version:
            return "base.change_minitraining"
        return "program_management.change_minitraining_version"

    def get_create_version_url(self):
        if self.is_root_node() and self.program_tree_version_identity.is_standard():
            return reverse(
                'create_education_group_version',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}
            ) + "?path={}".format(self.get_path())

    def get_create_version_permission_name(self) -> str:
        return "base.add_minitraining_version"

    def get_delete_permanently_tree_version_url(self):
        if not self.program_tree_version_identity.is_standard():
            return reverse(
                'delete_permanently_tree_version',
                kwargs={
                    'year': self.node_identity.year,
                    'code': self.node_identity.code,
                }
            )

    def get_delete_permanently_tree_version_permission_name(self):
        return "program_management.delete_permanently_minitraining_version"

    def get_delete_permanently_mini_training_url(self):
        if self.program_tree_version_identity.is_standard():
            return reverse(
                'mini_training_delete',
                kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}
            )

    def get_tab_urls(self):
        tab_urls = OrderedDict({
            Tab.IDENTIFICATION: {
                'text': _('Identification'),
                'active': Tab.IDENTIFICATION == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.IDENTIFICATION, self.node_identity, self.get_path()),
            },
            Tab.CONTENT: {
                'text': _('Content'),
                'active': Tab.CONTENT == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.CONTENT, self.node_identity, self.get_path()),
            },
            Tab.UTILIZATION: {
                'text': _('Utilizations'),
                'active': Tab.UTILIZATION == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.UTILIZATION, self.node_identity, self.get_path()),
            },
            Tab.GENERAL_INFO: {
                'text': _('General informations'),
                'active': Tab.GENERAL_INFO == self.active_tab,
                'display': self.have_general_information_tab(),
                'url': get_tab_urls(Tab.GENERAL_INFO, self.node_identity, self.get_path()),
            },
            Tab.SKILLS_ACHIEVEMENTS: {
                'text': capfirst(_('skills and achievements')),
                'active': Tab.SKILLS_ACHIEVEMENTS == self.active_tab,
                'display': self.have_skills_and_achievements_tab(),
                'url': get_tab_urls(Tab.SKILLS_ACHIEVEMENTS, self.node_identity, self.get_path()),
            },
            Tab.ADMISSION_CONDITION: {
                'text': _('Conditions'),
                'active': Tab.ADMISSION_CONDITION == self.active_tab,
                'display': self.have_admission_condition_tab(),
                'url': get_tab_urls(Tab.ADMISSION_CONDITION, self.node_identity, self.get_path()),
            },
        })

        return read.validate_active_tab(tab_urls)

    def have_general_information_tab(self):
        return self.current_version.is_standard_version and \
            self.get_group().type.name in general_information_sections.SECTIONS_PER_OFFER_TYPE

    def have_skills_and_achievements_tab(self):
        return self.current_version.is_standard_version and \
            self.get_group().type.name in MiniTrainingType.with_skills_achievements()

    def have_admission_condition_tab(self):
        return self.current_version.is_standard_version and \
            self.get_group().type.name in MiniTrainingType.with_admission_condition()

    def get_publish_url(self):
        return reverse('publish_general_information', args=[
            self.node_identity.year,
            self.node_identity.code
        ]) + "?path={}".format(self.get_path())


def _get_view_name_from_tab(tab: Tab):
    return {
        Tab.IDENTIFICATION: 'mini_training_identification',
        Tab.CONTENT: 'mini_training_content',
        Tab.UTILIZATION: 'mini_training_utilization',
        Tab.GENERAL_INFO: 'mini_training_general_information',
        Tab.SKILLS_ACHIEVEMENTS: 'mini_training_skills_achievements',
        Tab.ADMISSION_CONDITION: 'mini_training_admission_condition',
    }[tab]


def get_tab_urls(tab: Tab, node_identity: 'NodeIdentity', path: 'Path' = None) -> str:
    path = path or ""
    url_parameters = \
        "?path={}&tab={}#achievement_".format(path, tab) if tab == Tab.SKILLS_ACHIEVEMENTS else "?path={}".format(path)

    return reverse(
        _get_view_name_from_tab(tab),
        args=[node_identity.year, node_identity.code]
    ) + url_parameters
