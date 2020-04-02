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
import urllib

from django.http import JsonResponse, QueryDict
from django_filters.views import FilterView

from base.templatetags import pagination
from base.utils.cache import SearchParametersCache


class SearchMixin:
    """
        Search Mixin to return FilterView filter result as json when accept header is of type application/json.
        Implements method to return number of items per page.
        Add possibility to cache search parameters

        serializer_class: class used to serialize the resulting queryset
    """
    serializer_class = None
    cache_search = True

    def render_to_response(self, context, **response_kwargs):
        if "application/json" in self.request.headers.get("Accept", ""):
            serializer = self.serializer_class(
                context["page_obj"],
                context={
                    'request': self.request,
                    'language': self.request.LANGUAGE_CODE
                },
                many=True)
            return JsonResponse({
                'object_list': serializer.data,
                'total': context['paginator'].count,
            })
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.cache_search:
            SearchParametersCache(self.request.user, self.model.__name__).set_cached_data(self.request.GET)

        return context

    def get_paginate_by(self, queryset):
        pagination.store_paginator_size(self.request)
        return pagination.get_paginator_size(self.request)


class RenderToExcel:
    """
        View Mixin to generate excel when xls_status parameter is set.

        name: value of xls_status so as to generate the excel
        render_method: function to generate the excel.
                       The function must have as signature f(view_obj, context, **response_kwargs)
    """
    def __init__(self, name, render_method):
        self.name = name
        self.render_method = render_method

    def __call__(self, filter_class: FilterView):
        class Wrapped(filter_class):
            def render_to_response(obj, context, **response_kwargs):
                if obj.request.GET.get('xls_status') == self.name:
                    return self.render_method(obj, context, **response_kwargs)
                return super().render_to_response(context, **response_kwargs)
        return Wrapped
