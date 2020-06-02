##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import DetailView, FormView

from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.education_groups import perms
from base.views.education_groups.detail import CatalogGenericDetailView
from base.views.mixins import RulesRequiredMixin, FlagMixin, AjaxTemplateMixin
from osis_role.contrib.views import PermissionRequiredMixin, AjaxPermissionRequiredMixin
from program_management.ddd.repositories import load_tree
from program_management.models.enums.node_type import NodeType
from program_management.serializers import program_tree_view

NO_PREREQUISITES = TrainingType.finality_types() + [
    MiniTrainingType.OPTION.name,
    MiniTrainingType.MOBILITY_PARTNERSHIP.name,
] + GroupType.get_names()


@method_decorator(login_required, name='dispatch')
class GenericGroupElementYearMixin(AjaxPermissionRequiredMixin, FlagMixin, SuccessMessageMixin, AjaxTemplateMixin):
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

    def get_permission_object(self):
        return self.get_object().parent


@method_decorator(login_required, name='dispatch')
class LearningUnitGenericUpdateView(RulesRequiredMixin, SuccessMessageMixin, FormView):
    model = LearningUnitYear
    context_object_name = "learning_unit_year"
    pk_url_kwarg = 'learning_unit_year_id'

    raise_exception = True
    rules = [perms.can_change_education_group]

    def _call_rule(self, rule):
        return rule(self.request.user, self.get_root())

    def get_person(self):
        return get_object_or_404(Person, user=self.request.user)

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))

    @cached_property
    def program_tree(self):
        return load_tree.load(self.get_root().id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        root = self.get_root()
        serialized_data = program_tree_view.program_tree_view_serializer(self.program_tree)

        context['person'] = self.get_person()
        context['learning_unit_year'] = LearningUnitYear.objects.get(id=self.kwargs["learning_unit_year_id"])
        context['root'] = root
        context['root_id'] = self.kwargs.get("root_id")
        context['parent'] = root
        context['tree'] = json.dumps(serialized_data)

        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        return context


@method_decorator(login_required, name='dispatch')
class LearningUnitGenericDetailView(PermissionRequiredMixin, DetailView, CatalogGenericDetailView):
    model = LearningUnitYear
    context_object_name = "learning_unit_year"
    pk_url_kwarg = 'learning_unit_year_id'

    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def get_person(self):
        return get_object_or_404(Person, user=self.request.user)

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        root = self.get_root()

        self.program_tree = load_tree.load(root.id)
        serialized_data = program_tree_view.program_tree_view_serializer(self.program_tree)

        node = self.program_tree.get_node_by_id_and_type(self.object.id, NodeType.LEARNING_UNIT)

        context['person'] = self.get_person()
        context['root'] = root
        context['root_id'] = root.pk
        context['parent'] = root
        context['tree'] = json.dumps(serialized_data)
        context['node'] = node
        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        context['show_prerequisites'] = self.show_prerequisites(root)
        context['selected_element_clipboard'] = self.get_selected_element_for_clipboard()
        return context

    def show_prerequisites(self, education_group_year):
        return education_group_year.education_group_type.name not in NO_PREREQUISITES
