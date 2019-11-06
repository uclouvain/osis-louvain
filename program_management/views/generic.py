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
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import UpdateView, DetailView

from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.education_groups import perms
from base.views.education_groups.detail import CatalogGenericDetailView
from base.views.mixins import RulesRequiredMixin, FlagMixin, AjaxTemplateMixin
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy

NO_PREREQUISITES = TrainingType.finality_types() + [
    MiniTrainingType.OPTION.name,
    MiniTrainingType.MOBILITY_PARTNERSHIP.name,
] + GroupType.get_names()


@method_decorator(login_required, name='dispatch')
class GenericGroupElementYearMixin(FlagMixin, RulesRequiredMixin, SuccessMessageMixin, AjaxTemplateMixin):
    model = GroupElementYear
    context_object_name = "group_element_year"
    pk_url_kwarg = "group_element_year_id"

    # FlagMixin
    flag = "education_group_update"

    # RulesRequiredMixin
    raise_exception = True
    rules = [perms.can_change_education_group]

    def _call_rule(self, rule):
        """ The permission is computed from the education_group_year """
        return rule(self.request.user, self.education_group_year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['root'] = self.kwargs["root_id"]
        return context

    @property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("education_group_year_id"))

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))


@method_decorator(login_required, name='dispatch')
class LearningUnitGenericUpdateView(RulesRequiredMixin, SuccessMessageMixin, UpdateView):
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
    def education_group_year_hierarchy(self):
        return EducationGroupHierarchy(self.get_root())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        root = self.get_root()
        context['person'] = self.get_person()
        context['root'] = root
        context['root_id'] = self.kwargs.get("root_id")
        context['parent'] = root
        context['tree'] = json.dumps(self.education_group_year_hierarchy.to_json())

        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        return context


@method_decorator(login_required, name='dispatch')
class LearningUnitGenericDetailView(PermissionRequiredMixin, DetailView, CatalogGenericDetailView):
    model = LearningUnitYear
    context_object_name = "learning_unit_year"
    pk_url_kwarg = 'learning_unit_year_id'

    permission_required = 'base.can_access_education_group'
    raise_exception = True

    def get_person(self):
        return get_object_or_404(Person, user=self.request.user)

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        root = self.get_root()
        self.hierarchy = EducationGroupHierarchy(root, tab_to_show=self.request.GET.get("tab_to_show"))
        # TODO remove parent in context
        context['person'] = self.get_person()
        context['root'] = root
        context['root_id'] = root.pk
        context['parent'] = root
        context['tree'] = json.dumps(self.hierarchy.to_json())
        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        context['show_prerequisites'] = self.show_prerequisites(root)
        context['selected_element_clipboard'] = self.get_selected_element_for_clipboard()
        return context

    def show_prerequisites(self, education_group_year):
        return education_group_year.education_group_type.name not in NO_PREREQUISITES
