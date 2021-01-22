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
from django.db.models import Prefetch

import program_management.ddd.repositories.find_roots
from base.models.education_group_year import EducationGroupYear
from base.models.prerequisite import Prerequisite
from base.views.common import display_business_warning_messages
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.validators._authorized_root_type_for_prerequisite import AuthorizedRootTypeForPrerequisite
from program_management.ddd.validators._prerequisites_items import PrerequisiteItemsValidator
from program_management.views.generic import LearningUnitGeneric, Tab


class LearningUnitPrerequisite(PermissionRequiredMixin, LearningUnitGeneric):
    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if self.program_tree.root_node.is_group():
            return LearningUnitPrerequisiteGroup.as_view()(request, *args, **kwargs)
        return LearningUnitPrerequisiteTrainingandMiniTraining.as_view()(request, *args, **kwargs)

    def get_permission_object(self):
        return GroupYear.objects.get(element__pk=self.program_tree.root_node.pk)


class LearningUnitPrerequisiteTrainingandMiniTraining(PermissionRequiredMixin, LearningUnitGeneric):
    template_name = "learning_unit/tab_prerequisite_training.html"
    active_tab = Tab.PREREQUISITE

    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["can_modify_prerequisite"] = self.request.user.has_perm(
            'base.change_prerequisite',
            self.get_permission_object()
        )
        context["show_modify_prerequisite_button"] = AuthorizedRootTypeForPrerequisite(
            self.program_tree.root_node
        ).is_valid()
        context["program_links"] = self.program_tree.get_all_links()
        context["is_prerequisite_of_list"] = self.program_tree.search_is_prerequisite_of(context["node"])
        context["prerequisite"] = self.program_tree.get_prerequisite(context["node"])
        return context

    def render_to_response(self, context, **response_kwargs):
        self.add_warning_messages(context)
        return super().render_to_response(context, **response_kwargs)

    def add_warning_messages(self, context):
        validator = PrerequisiteItemsValidator(
            str(self.program_tree.get_prerequisite(self.node)),
            self.node,
            self.program_tree
        )
        if not validator.is_valid():
            display_business_warning_messages(
                self.request,
                validator.messages
            )

    def get_permission_object(self):
        return GroupYear.objects.get(element__pk=self.program_tree.root_node.pk)


class LearningUnitPrerequisiteGroup(PermissionRequiredMixin, LearningUnitGeneric):
    template_name = "learning_unit/tab_prerequisite_group.html"
    active_tab = Tab.PREREQUISITE

    permission_required = 'base.view_educationgroup'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        # TODO : Use DDD for this part
        learning_unit_year = context["learning_unit_year"]
        formations_id = program_management.ddd.repositories.find_roots.find_roots([learning_unit_year]).get(
            learning_unit_year.id,
            []
        )
        qs = EducationGroupYear.objects.filter(id__in=formations_id)
        prefetch_prerequisites = Prefetch(
            "prerequisite_set",
            Prerequisite.objects.filter(learning_unit_year=learning_unit_year),
            to_attr="prerequisites"
        )
        context["formations"] = qs.prefetch_related(prefetch_prerequisites)
        return context

    def get_permission_object(self):
        return GroupYear.objects.get(element__pk=self.program_tree.root_node.pk)
