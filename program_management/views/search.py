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
import itertools
from collections import OrderedDict

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.forms.search.search_form import get_research_criteria
from base.models.academic_year import starting_academic_year
from base.models.education_group_type import EducationGroupType
from education_group.models.group_year import GroupYear
from base.models.enums import education_group_categories
from base.models.person import Person
from base.utils.cache import CacheFilterMixin
from base.utils.search import SearchMixin

from program_management.api.serializers.education_group import EducationGroupSerializer
from program_management.forms.education_groups import GroupFilter


def _get_filter(form):
    return OrderedDict(itertools.chain(get_research_criteria(form)))


class EducationGroupSearch(LoginRequiredMixin, PermissionRequiredMixin, CacheFilterMixin, SearchMixin, FilterView):
    model = GroupYear
    template_name = "search.html"
    raise_exception = False

    filterset_class = GroupFilter
    permission_required = 'base.can_access_education_group'

    serializer_class = EducationGroupSerializer

    def get_context_data(self, **kwargs):
        person = get_object_or_404(Person, user=self.request.user)
        context = super().get_context_data(**kwargs)
        starting_ac = starting_academic_year()
        if context["paginator"].count == 0 and self.request.GET:
            messages.add_message(self.request, messages.WARNING, _('No result!'))
        context.update({
            'person': person,
            'form': context["filter"].form,
            'object_list_count': context["paginator"].count,
            'current_academic_year': starting_ac,
            'items_per_page': context["paginator"].per_page,
            'enums': education_group_categories,
        })
        return context


class EducationGroupTypeAutoComplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return EducationGroupType.objects.none()

        qs = EducationGroupType.objects.all()

        category = self.forwarded.get('category', None)
        if category:
            qs = qs.filter(category=category)
        if self.q:
            # Filtering must be done in python because translated value.
            ids_to_keep = {result.pk for result in qs if self.q.lower() in result.get_name_display().lower()}
            qs = qs.filter(id__in=ids_to_keep)

        qs = qs.order_by_translated_name()
        return qs

    def get_result_label(self, result):
        return format_html('{}', result.get_name_display())
