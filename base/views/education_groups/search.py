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

from base.business.education_group import create_xls, ORDER_COL, ORDER_DIRECTION, create_xls_administrative_data
from base.forms.education_groups import EducationGroupFilter
from base.forms.search.search_form import get_research_criteria
from base.models.academic_year import starting_academic_year
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.person import Person
from base.utils.cache import CacheFilterMixin
from base.utils.search import RenderToExcel, SearchMixin
from base.views.education_groups.perms import FlagNotAuthorized
from education_group.api.serializers.education_group import EducationGroupSerializer


def _get_filter(form):
    return OrderedDict(itertools.chain(get_research_criteria(form)))


def _create_xls(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    egys = context["filter"].qs
    filters = _get_filter(context["form"])
    # FIXME: use ordering args in filter_form! Remove xls_order_col/xls_order property
    order = {ORDER_COL: view_obj.request.GET.get('xls_order_col'),
             ORDER_DIRECTION: view_obj.request.GET.get('xls_order')}
    return create_xls(user, egys, filters, order)


def _create_xls_administrative_data(view_obj, context, **response_kwargs):
    user = view_obj.request.user
    egys = context["filter"].qs
    filters = _get_filter(context["form"])
    # FIXME: use ordering args in filter_form! Remove xls_order_col/xls_order property
    order = {ORDER_COL: view_obj.request.GET.get('xls_order_col'),
             ORDER_DIRECTION: view_obj.request.GET.get('xls_order')}
    return create_xls_administrative_data(user, egys, filters, order)


@RenderToExcel("xls_administrative", _create_xls_administrative_data)
@RenderToExcel("xls", _create_xls)
class EducationGroupSearch(LoginRequiredMixin, FlagNotAuthorized, PermissionRequiredMixin, CacheFilterMixin,
                           SearchMixin, FilterView):
    model = EducationGroupYear
    template_name = "education_group/search.html"
    raise_exception = False

    filterset_class = EducationGroupFilter
    permission_required = 'base.can_access_education_group'
    flag_not_authorized = 'version_program'

    cache_exclude_params = 'xls_status'

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
