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
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django_filters import FilterSet, filters, OrderingFilter
from django_filters.views import FilterView

from base.forms.learning_unit.search.quick_search import QuickLearningUnitYearFilter
from base.models.academic_year import AcademicYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin
from base.utils.urls import reverse_with_get
from base.views.mixins import AjaxTemplateMixin
from education_group.views.serializers.group_year import GroupYearSerializer
from education_group.models.group_year import GroupYear
from learning_unit.api.serializers.learning_unit import LearningUnitSerializer

CACHE_TIMEOUT = 60


class QuickGroupYearFilter(FilterSet):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        to_field_name="year",
        required=False,
        label=_('Ac yr.'),
        empty_label=pgettext_lazy("female plural", "All"),
    )
    acronym = filters.CharFilter(
        field_name="acronym",
        lookup_expr='icontains',
        max_length=40,
        required=False,
        label=_('Acronym/Short title'),
    )
    partial_acronym = filters.CharFilter(
        field_name="partial_acronym",
        lookup_expr='icontains',
        max_length=40,
        required=False,
        label=_('Code'),
    )
    title = filters.CharFilter(
        field_name="title_fr",
        lookup_expr='icontains',
        max_length=255,
        required=False,
        label=_('Title')
    )

    ordering = OrderingFilter(
        fields=(
            ('academic_year__year', 'academic_year'),
            ('acronym', 'acronym'),
            ('partial_acronym', 'code'),
            ('title_fr', 'title'),
        ),
        widget=forms.HiddenInput
    )

    class Meta:
        model = GroupYear
        fields = [
            'acronym',
            'title',
            'academic_year',
            'partial_acronym'
        ]

    def __init__(self, *args, initial=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()
        if initial:
            self.form.fields["academic_year"].initial = initial["academic_year"]

    def get_queryset(self):
        # Need this close so as to return empty query by default when form is unbound
        # 'changed_data' has been used instead of 'has_changed' here because the hidden field 'academic_year'
        # which never is empty so need to check the 3 other fields of the form
        watched_form_fields = ['acronym', 'partial_acronym', 'title']
        if not self.data or not any(field in self.form.changed_data for field in watched_form_fields):
            return GroupYear.objects.none()
        return GroupYear.objects.all()


class QuickSearchGroupYearView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, SearchMixin,
                               FilterView):
    model = GroupYear
    template_name = 'quick_search_egy_inner.html'
    permission_required = ['base.view_educationgroup', 'base.can_access_learningunit']
    timeout = CACHE_TIMEOUT

    filterset_class = QuickGroupYearFilter
    cache_exclude_params = ['page', 'path']
    paginate_by = "12"
    ordering = ('academic_year', 'acronym', 'partial_acronym')

    serializer_class = GroupYearSerializer

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        queryparams = kwargs['data'].copy()
        del queryparams["path"]
        if "academic_year" not in queryparams:
            queryparams["academic_year"] = self.kwargs["year"]
        kwargs["data"] = queryparams
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['display_quick_search_luy_link'] = self.is_learning_unit_child_allowed()
        context['node_path'] = self.request.GET["path"]
        context['year'] = self.kwargs["year"]
        context['quick_search_learning_unit_url'] = self.get_quick_search_learning_unit_url()
        return context

    def render_to_response(self, context, **response_kwargs):
        # 'changed_data' has been used instead of 'has_changed' here because the hidden field 'academic_year'
        # which never is empty so need to check the 3 other fields of the form
        watched_form_fields = ['acronym', 'partial_acronym', 'title']
        if context["form"].is_valid() and not context["paginator"].count and \
                any(field in context["form"].changed_data for field in watched_form_fields):
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by

    def is_learning_unit_child_allowed(self):
        element_id = int(self.request.GET["path"].split("|")[-1])
        return GroupYear.objects.get(element__id=element_id).education_group_type.learning_unit_child_allowed

    def get_quick_search_learning_unit_url(self):
        queryparams = {'path': self.request.GET['path']} if 'path' in self.request.GET else {}
        return reverse_with_get(
            "quick_search_learning_unit",
            args=[self.kwargs['year']],
            get=queryparams
        )


class QuickSearchLearningUnitYearView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, SearchMixin,
                                      FilterView):
    model = LearningUnitYear
    template_name = 'quick_search_luy_inner.html'
    permission_required = ['base.view_educationgroup', 'base.can_access_learningunit']
    timeout = CACHE_TIMEOUT

    filterset_class = QuickLearningUnitYearFilter
    cache_exclude_params = ['page', 'path']
    paginate_by = "12"
    ordering = ('academic_year', 'acronym')

    serializer_class = LearningUnitSerializer

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        queryparams = kwargs['data'].copy()
        del queryparams["path"]
        if "academic_year" not in queryparams:
            queryparams["academic_year"] = self.kwargs["year"]
        kwargs["data"] = queryparams
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = context["filter"].form
        context['node_path'] = self.request.GET["path"]
        context['year'] = self.kwargs["year"]
        context['quick_search_education_group_url'] = self.get_quick_search_education_group_url()
        return context

    def render_to_response(self, context, **response_kwargs):
        # 'changed_data' has been used instead of 'has_changed' here because the hidden field 'academic_year'
        # which never is empty so need to check the 2 other fields of the form
        watched_form_fields = ['acronym', 'title']
        if context["form"].is_valid() and not context["paginator"].count and \
                any(field in context["form"].changed_data for field in watched_form_fields):
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        return super().render_to_response(context, **response_kwargs)

    def get_paginate_by(self, queryset):
        return self.paginate_by

    def get_quick_search_education_group_url(self):
        queryparams = {'path': self.request.GET['path']} if 'path' in self.request.GET else {}
        return reverse_with_get(
            "quick_search_education_group",
            args=[self.kwargs['year']],
            get=queryparams
        )
