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
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.forms.education_group.search.quick_search import QuickGroupYearFilter
from base.forms.learning_unit.search.quick_search import QuickLearningUnitYearFilter
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin
from base.views.mixins import AjaxTemplateMixin
from education_group.views.serializers.group_year import GroupYearSerializer
from education_group.models.group_year import GroupYear
from learning_unit.api.serializers.learning_unit import LearningUnitSerializer

CACHE_TIMEOUT = 60


class QuickSearchGroupYearView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, SearchMixin,
                               FilterView):
    model = GroupYear
    template_name = 'quick_search_egy_inner.html'
    permission_required = ['base.view_educationgroup', 'base.can_access_learningunit']
    timeout = CACHE_TIMEOUT

    filterset_class = QuickGroupYearFilter
    cache_exclude_params = ['page']
    paginate_by = "12"
    ordering = ('academic_year', 'acronym', 'partial_acronym')

    serializer_class = GroupYearSerializer

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["initial"] = {'academic_year': self.kwargs["year"]}
        get_without_path = kwargs['data'].copy()  # type: QueryDict
        del get_without_path["path"]
        kwargs["data"] = get_without_path or None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['display_quick_search_luy_link'] = self.is_learning_unit_child_allowed()
        context['node_path'] = self.request.GET["path"]
        context['year'] = self.kwargs["year"]
        return context

    def render_to_response(self, context, **response_kwargs):
        if context["form"].is_valid() and not context["paginator"].count:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by

    def is_learning_unit_child_allowed(self):
        element_id = int(self.request.GET["path"].split("|")[-1])
        return GroupYear.objects.get(element__id=element_id).education_group_type.learning_unit_child_allowed


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

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["initial"] = {'academic_year': self.kwargs["year"]}
        get_without_path = kwargs['data'].copy()  # type: QueryDict
        del get_without_path["path"]
        kwargs["data"] = get_without_path or None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['node_path'] = self.request.GET["path"]
        context['year'] = self.kwargs["year"]
        return context

    def render_to_response(self, context, **response_kwargs):
        if context["form"].is_valid() and not context["paginator"].count:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by
