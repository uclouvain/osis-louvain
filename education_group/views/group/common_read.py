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

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from base import models as mdl
from base.business.education_groups import general_information_sections
from base.models import academic_year
from base.models.enums.education_group_categories import Categories
from base.utils.urls import reverse_with_get
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.service.read import get_group_service
from education_group.forms.academic_year_choices import get_academic_year_choices
from education_group.models.group_year import GroupYear
from education_group.views.mixin import ElementSelectedClipBoardMixin
from education_group.views.proxy import read
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.business_types import *
from program_management.ddd import command as command_program_management
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.service.read import node_identity_service
from program_management.forms.custom_xls import CustomXlsForm
from program_management.models.element import Element

Tab = read.Tab  # FIXME :: fix imports (and remove this line)


class GroupRead(PermissionRequiredMixin, ElementSelectedClipBoardMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    active_tab = None

    @functools.lru_cache()
    def get_path(self) -> str:
        path = self.request.GET.get('path')
        if path is None:
            root_element = Element.objects.get(
                group_year__academic_year__year=self.kwargs['year'],
                group_year__partial_acronym=self.kwargs['code'].upper()
            )
            path = str(root_element.pk)
        return path

    def get_root_id(self) -> int:
        return int(self.get_path().split("|")[0])

    @cached_property
    def is_root_node(self) -> bool:
        node_identity = node_identity_service.get_node_identity_from_element_id(
            command_program_management.GetNodeIdentityFromElementId(element_id=self.get_root_id())
        )
        return node_identity == self.node_identity

    @cached_property
    def node_identity(self) -> 'NodeIdentity':
        return NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "person": self.request.user.person,
            "enums": mdl.enums.education_group_categories,
            "form_xls_custom": CustomXlsForm(year=self.get_group().year, code=self.get_group().code),
            "group": self.get_group(),
            "node_path": self.get_path(),
            "tab_urls": self.get_tab_urls(),
            "academic_year_choices": get_academic_year_choices(
                self.node_identity,
                self.get_path(),
                _get_view_name_from_tab(self.active_tab)
            ) if self.is_root_node else None,
            "xls_ue_prerequisites": reverse("education_group_learning_units_prerequisites",
                                            args=[self.get_group_year().academic_year.year,
                                                  self.get_group_year().partial_acronym]
                                            ),
            "xls_ue_is_prerequisite": reverse("education_group_learning_units_is_prerequisite_for",
                                              args=[self.get_group_year().academic_year.year,
                                                    self.get_group_year().partial_acronym]
                                              ),
            "generate_pdf_url": reverse("group_pdf_content",
                                        args=[
                                            self.get_group_year().academic_year.year,
                                            self.get_group_year().partial_acronym,
                                        ],
                                        ),
            "selected_element_clipboard": self.get_selected_element_clipboard_message(),
            "group_year": self.get_group_year(),  # TODO: Should be remove and use DDD object
            "create_group_url": self.get_create_group_url(),
            "update_group_url": self.get_update_group_url(),
            "update_permission_name": self.get_update_permission_name(),
            "delete_group_url": self.get_delete_group_url(),
            "create_training_url": self.get_create_training_url(),
            "create_mini_training_url": self.get_create_mini_training_url(),
            "tree_json_url": self.get_tree_json_url(),
            "tree_root_id": self.get_root_id(),
            "is_root_node": self.is_root_node,
        }

    @functools.lru_cache()
    def get_group_year(self) -> 'GroupYear':
        return get_object_or_404(
            GroupYear.objects.select_related('education_group_type', 'academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )

    @functools.lru_cache()
    def get_group(self) -> 'Group':
        get_group_cmd = command.GetGroupCommand(year=self.kwargs['year'], code=self.kwargs['code'])
        return get_group_service.get_group(get_group_cmd)

    @functools.lru_cache()
    def get_current_academic_year(self):
        return academic_year.starting_academic_year()

    def get_permission_object(self):
        return self.get_group_year()

    def get_create_group_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.GROUP.name}) + \
               "?path_to={}".format(self.get_path())

    def get_update_group_url(self):
        return reverse('group_update', kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}) + \
               "?path={}".format(self.get_path())

    def get_update_permission_name(self) -> str:
        return "base.change_group"

    def get_create_mini_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.MINI_TRAINING.name}) + \
               "?path_to={}".format(self.get_path())

    def get_create_training_url(self):
        return reverse('create_element_select_type', kwargs={'category': Categories.TRAINING.name}) + \
               "?path_to={}".format(self.get_path())

    def get_delete_group_url(self):
        return reverse('group_delete', kwargs={'year': self.node_identity.year, 'code': self.node_identity.code}) + \
               "?path={}".format(self.get_path())

    def get_tree_json_url(self) -> str:
        return reverse_with_get(
            'tree_json',
            kwargs={'root_id': self.get_root_id()},
            get={"path": self.get_path()}
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
            }
        })

        return read.validate_active_tab(tab_urls)

    def have_general_information_tab(self):
        return self.get_group().type.name in general_information_sections.SECTIONS_PER_OFFER_TYPE


def _get_view_name_from_tab(tab: Tab):
    return {
        Tab.IDENTIFICATION: 'group_identification',
        Tab.CONTENT: 'group_content',
        Tab.UTILIZATION: 'group_utilization',
        Tab.GENERAL_INFO: 'group_general_information',
    }[tab]


def get_tab_urls(tab: Tab, node_identity: 'NodeIdentity', path: 'Path' = None) -> str:
    path = path or ""
    return reverse(
        _get_view_name_from_tab(tab),
        args=[node_identity.year, node_identity.code]
    ) + "?path={}".format(path)
