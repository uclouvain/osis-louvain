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
import json

from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.utils.cache import ElementCache
from base.views.mixins import FlagMixin, AjaxTemplateMixin
from education_group.models.group_year import GroupYear
from osis_common.utils.models import get_object_or_none
from osis_role.contrib.views import AjaxPermissionRequiredMixin
from program_management.ddd.repositories import load_tree
from program_management.models.enums.node_type import NodeType
from program_management.ddd.business_types import *
from program_management.serializers.program_tree_view import program_tree_view_serializer
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.domain.node import NodeIdentity

NO_PREREQUISITES = TrainingType.finality_types() + [
    MiniTrainingType.OPTION.name,
    MiniTrainingType.MOBILITY_PARTNERSHIP.name,
] + GroupType.get_names()


LEARNING_UNIT_YEAR = LearningUnitYear._meta.db_table
EDUCATION_GROUP_YEAR = EducationGroupYear._meta.db_table


def get_clipboard_content_display(obj, action):
    msg_template = "<strong>{clipboard_title}</strong><br>{object_str}"
    return msg_template.format(
        clipboard_title=_get_clipboard_title(action),
        object_str=str(obj),
    )


def _get_clipboard_title(action):
    if action == ElementCache.ElementCacheAction.CUT.value:
        return _("Cut element")
    elif action == ElementCache.ElementCacheAction.COPY.value:
        return _("Copied element")
    else:
        return ""


class CatalogGenericDetailView:
    def get_selected_element_for_clipboard(self):
        cached_data = ElementCache(self.request.user).cached_data
        if cached_data:
            obj = self._get_instance_object_from_cache(cached_data)
            return get_clipboard_content_display(obj, cached_data['action'])
        return None

    @staticmethod
    def _get_instance_object_from_cache(cached_data):
        model_name = cached_data.get('modelname')
        cached_obj_id = cached_data.get('id')
        obj = None
        if model_name == LEARNING_UNIT_YEAR:
            obj = LearningUnitYear.objects.get(id=cached_obj_id)
        elif model_name == EDUCATION_GROUP_YEAR:
            obj = EducationGroupYear.objects.get(id=cached_obj_id)
        return obj


@method_decorator(login_required, name='dispatch')
class GenericGroupElementYearMixin(FlagMixin, AjaxPermissionRequiredMixin, SuccessMessageMixin, AjaxTemplateMixin):
    model = GroupElementYear
    context_object_name = "group_element_year"
    pk_url_kwarg = "group_element_year_id"

    # FlagMixin
    flag = "education_group_update"

    permission_required = 'base.change_link_data'

    @property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("education_group_year_id"))

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))

    def get_permission_object(self) -> GroupYear:
        return self.get_object().parent_element.group_year


class LearningUnitGeneric(CatalogGenericDetailView, TemplateView):
    def get_person(self):
        return get_object_or_404(Person, user=self.request.user)

    @cached_property
    def program_tree(self):
        return load_tree.load(int(self.kwargs['root_element_id']))

    @cached_property
    def node(self):
        node = self.program_tree.get_node_by_id_and_type(
            int(self.kwargs['child_element_id']),
            NodeType.LEARNING_UNIT
        )
        if node is None:
            raise Http404
        return node

    @cached_property
    def program_tree_version_identity(self) -> 'ProgramTreeVersionIdentity':
        return ProgramTreeVersionIdentitySearch().get_from_node_identity(
            NodeIdentity(code=self.program_tree.root_node.code, year=self.program_tree.root_node.year))

    @cached_property
    def current_version(self) -> 'ProgramTreeVersion':
        return ProgramTreeVersionRepository.get(self.program_tree_version_identity)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['person'] = self.get_person()
        # TODO: use DDD instead
        root = GroupYear.objects.get(element__pk=self.program_tree.root_node.pk)
        context['root'] = root
        context['root_id'] = self.program_tree.root_node.pk
        context['parent'] = self.program_tree.root_node
        context['node'] = self.node
        context['tree'] = json.dumps(program_tree_view_serializer(self.current_version.get_tree()))
        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        context['show_prerequisites'] = self.show_prerequisites(self.program_tree.root_node)
        context['selected_element_clipboard'] = self.get_selected_element_for_clipboard()
        context['xls_ue_prerequisites'] = reverse("education_group_learning_units_prerequisites",
                                                  args=[root.academic_year.year, root.partial_acronym]
                                                  )
        context['xls_ue_is_prerequisite'] = reverse("education_group_learning_units_is_prerequisite_for",
                                                    args=[root.academic_year.year, root.partial_acronym]
                                                    )
        # TODO: Remove when DDD is implemented on learning unit year...
        context['learning_unit_year'] = get_object_or_none(
            LearningUnitYear,
            element__pk=self.kwargs['child_element_id']
        )
        return context

    def show_prerequisites(self, root_node: 'NodeGroupYear'):
        return root_node.node_type not in NO_PREREQUISITES

    def get_permission_object(self):
        return GroupYear.objects.get(element__pk=self.program_tree.root_node.pk)
