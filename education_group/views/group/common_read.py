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
import functools
import json
from collections import OrderedDict
from enum import Enum

from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from base import models as mdl
from base.business.education_groups import general_information_sections
from base.business.education_groups.general_information_sections import \
    MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION
from base.models import academic_year
from base.models.enums.education_group_types import GroupType
from base.utils.cache import ElementCache
from base.views.common import display_warning_messages
from education_group.forms.academic_year_choices import get_academic_year_choices
from education_group.models.group_year import GroupYear
from education_group.views.mixin import ElementSelectedClipBoardMixin
from education_group.views.proxy import read
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeIdentity, NodeNotFoundException
from program_management.ddd.repositories import load_tree
from program_management.ddd.service.read import element_selected_service
from program_management.forms.custom_xls import CustomXlsForm
from program_management.models.element import Element
from program_management.serializers.program_tree_view import program_tree_view_serializer


Tab = read.Tab  # FIXME :: fix imports (and remove this line)


class GroupRead(PermissionRequiredMixin, ElementSelectedClipBoardMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    active_tab = None

    def get(self, request, *args, **kwargs):
        self.path = self.request.GET.get('path')
        if self.path is None:
            root_element = Element.objects.get(
                group_year__academic_year__year=self.kwargs['year'],
                group_year__partial_acronym=self.kwargs['code']
            )
            self.path = str(root_element.pk)
        return super().get(request, *args, **kwargs)

    @functools.lru_cache()
    def get_tree(self):
        root_element_id = self.path.split("|")[0]
        return load_tree.load(int(root_element_id))

    @cached_property
    def node_identity(self) -> 'NodeIdentity':
        return NodeIdentity(code=self.kwargs['code'], year=self.kwargs['year'])

    @functools.lru_cache()
    def get_object(self) -> 'Node':
        try:
            return self.get_tree().get_node(self.path)
        except NodeNotFoundException:
            root_node = self.get_tree().root_node
            message = _(
                "The formation you work with doesn't exist (or is not at the same position) "
                "in the tree {root.title} in {root.year}."
                "You've been redirected to the root {root.code} ({root.year})"
            ).format(root=root_node)
            display_warning_messages(self.request, message)
            return root_node

    def get_context_data(self, **kwargs):
        can_change_education_group = self.request.user.has_perm(
            'base.change_educationgroup',
            self.get_permission_object()
        )
        return {
            **super().get_context_data(**kwargs),
            "person": self.request.user.person,
            "enums": mdl.enums.education_group_categories,
            "can_change_education_group": can_change_education_group,
            "form_xls_custom": CustomXlsForm(),
            "tree": json.dumps(program_tree_view_serializer(self.get_tree())),
            "node": self.get_object(),
            "tab_urls": self.get_tab_urls(),
            "academic_year_choices": get_academic_year_choices(
                self.node_identity,
                self.path,
                _get_view_name_from_tab(self.active_tab),
            ),
            "selected_element_clipboard": self.get_selected_element_clipboard_message(),
            "group_year": self.get_group_year()  # TODO: Should be remove and use DDD object
        }

    @functools.lru_cache()
    def get_group_year(self):
        try:
            return GroupYear.objects.select_related('education_group_type', 'academic_year', 'management_entity')\
                                .get(academic_year__year=self.kwargs['year'], partial_acronym=self.kwargs['code'])
        except GroupYear.DoesNotExist:
            raise Http404

    @functools.lru_cache()
    def get_current_academic_year(self):
        return academic_year.starting_academic_year()

    def get_permission_object(self):
        return self.get_group_year()

    def get_tab_urls(self):
        return OrderedDict({
            Tab.IDENTIFICATION: {
                'text': _('Identification'),
                'active': Tab.IDENTIFICATION == self.active_tab,
                'display': True,
                'url': get_tab_urls(Tab.IDENTIFICATION, self.node_identity, self.path),
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
            }
        })

    def have_general_information_tab(self):
        return self.get_object().node_type.name in general_information_sections.SECTIONS_PER_OFFER_TYPE and \
            self._is_general_info_and_condition_admission_in_display_range

    def _is_general_info_and_condition_admission_in_display_range(self):
        return MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION <= self.get_object().year < \
               self.get_current_academic_year().year + 2


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
