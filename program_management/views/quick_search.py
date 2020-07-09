# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from django.utils.translation import gettext_lazy as _

from base.forms.education_group.search.quick_search import QuickEducationGroupYearFilter
from base.forms.learning_unit.search.quick_search import QuickLearningUnitYearFilter
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin
from base.views.mixins import AjaxTemplateMixin
from education_group.api.serializers.education_group import EducationGroupSerializer
from learning_unit.api.serializers.learning_unit import LearningUnitSerializer
from program_management.business.group_element_years import attach
from program_management.ddd.repositories import load_node

CACHE_TIMEOUT = 60


class QuickSearchEducationGroupYearView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, SearchMixin,
                                        FilterView):
    model = EducationGroupYear
    template_name = 'quick_search_egy_inner.html'
    permission_required = ['base.view_educationgroup', 'base.can_access_learningunit']
    timeout = CACHE_TIMEOUT

    filterset_class = QuickEducationGroupYearFilter
    cache_exclude_params = ['page']
    paginate_by = "12"
    ordering = ('academic_year', 'acronym', 'partial_acronym')

    serializer_class = EducationGroupSerializer

    @property
    def node_id(self) -> int:
        return int(self.kwargs["node_path"].split("|")[-1])

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        node = load_node.load_node_education_group_year(self.node_id)
        kwargs["initial"] = {'academic_year': node.year}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['root_id'] = self.kwargs['root_id']
        context['education_group_year_id'] = self.node_id
        context['display_quick_search_luy_link'] = attach.can_attach_learning_units(
            EducationGroupYear.objects.get(id=self.node_id)
        )
        context['node_path'] = self.kwargs["node_path"]
        return context

    def render_to_response(self, context, **response_kwargs):
        if context["form"].is_valid() and not context["paginator"].count:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by


class QuickSearchLearningUnitYearView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, SearchMixin,
                                      FilterView):
    model = LearningUnitYear
    template_name = 'quick_search_luy_inner.html'
    permission_required = ['base.view_educationgroup', 'base.can_access_learningunit']
    timeout = CACHE_TIMEOUT

    filterset_class = QuickLearningUnitYearFilter
    cache_exclude_params = ['page']
    paginate_by = "12"
    ordering = ('academic_year', 'acronym')

    serializer_class = LearningUnitSerializer

    @property
    def node_id(self) -> int:
        return int(self.kwargs["node_path"].split("|")[-1])

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        node = load_node.load_node_education_group_year(self.node_id)
        kwargs["initial"] = {'academic_year': node.year}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['root_id'] = self.kwargs['root_id']
        context['education_group_year_id'] = self.node_id
        context['node_path'] = self.kwargs["node_path"]
        return context

    def render_to_response(self, context, **response_kwargs):
        if context["form"].is_valid() and not context["paginator"].count:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by
