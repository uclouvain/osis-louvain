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
from abc import ABC

from django import forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.views.generic import ListView

from base.models.academic_year import starting_academic_year, AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.views.mixins import AjaxTemplateMixin


class QuickSearchForm(forms.Form):
    academic_year = forms.ModelChoiceField(AcademicYear.objects.all(), required=True)
    search_text = forms.CharField(required=False)


class QuickSearchGenericView(PermissionRequiredMixin, CacheFilterMixin, AjaxTemplateMixin, ListView, ABC):
    """ Quick search generic view for learning units and education group year """
    paginate_by = "12"
    ordering = 'academic_year', 'acronym',
    template_name = 'base/quick_search_inner.html'
    cache_exclude_params = 'page',

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.GET.get('academic_year'):
            qs = qs.filter(academic_year=self.request.GET.get('academic_year'))

        search_text = self.request.GET.get('search_text')
        if search_text:
            qs = self.search_text_filter(qs, search_text)

        return qs

    def search_text_filter(self, qs, search_text):
        raise NotImplementedError

    def paginate_queryset(self, queryset, page_size):
        """ The cache can store a wrong page number,
        In that case, we return to the first page.
        """
        try:
            return super().paginate_queryset(queryset, page_size)
        except Http404:
            self.kwargs['page'] = 1

        return super().paginate_queryset(queryset, page_size)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        academic_yr = AcademicYear.objects.get(pk=self.request.GET.get('academic_year')) \
            if self.request.GET.get('academic_year') else starting_academic_year()

        context['form'] = QuickSearchForm(
            initial={
                'academic_year': academic_yr,
                'search_text': self.request.GET.get('search_text', ''),
            }
        )

        # Save in session the last model used in the quick search.
        self.request.session['quick_search_model'] = self.model.__name__
        return context


class QuickSearchLearningUnitYearView(QuickSearchGenericView):
    model = LearningUnitYear
    permission_required = 'base.can_access_learningunit'

    def search_text_filter(self, qs, search_text):
        return qs.filter(
            Q(acronym__icontains=search_text) | Q(specific_title__icontains=search_text)
        ).select_related('learning_container_year')


class QuickSearchEducationGroupYearView(QuickSearchGenericView):
    model = EducationGroupYear
    permission_required = 'base.can_access_education_group'

    def search_text_filter(self, qs, search_text):
        return qs.filter(
            Q(acronym__icontains=search_text) |
            Q(title__icontains=search_text) |
            Q(title_english__icontains=search_text) |
            Q(partial_acronym__icontains=search_text)
        )
