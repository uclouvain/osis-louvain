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
import abc
import logging
from enum import Enum
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import QueryDict

CACHE_FILTER_TIMEOUT = None
PREFIX_CACHE_KEY = 'cache_filter'

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def cache_filter(exclude_params=None, **default_values):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            try:
                request_cache = RequestCache(user=request.user, path=request.path)
                if request.GET:
                    request_cache.save_get_parameters(request, parameters_to_exclude=exclude_params)
                request.GET = request_cache.restore_get_request(request, **default_values)
            except Exception:
                logger.exception('An error occurred with cache system')
            return func(request, *args, **kwargs)

        return inner

    return decorator


class CacheFilterMixin:
    cache_exclude_params = None
    timeout = None

    # Mixin that keep the cache for cbv.
    def get(self, request, *args, **kwargs):
        request_cache = RequestCache(user=request.user, path=request.path)
        if self.__have_data_to_cached(request):
            request_cache.save_get_parameters(
                request,
                parameters_to_exclude=self.cache_exclude_params,
                timeout=self.timeout
            )
        request.GET = request_cache.restore_get_request(request)
        return super().get(request, *args, **kwargs)

    def __have_data_to_cached(self, request) -> bool:
        return bool(set(request.GET.keys()) - set(self.cache_exclude_params or []))


class OsisCache(abc.ABC):
    PREFIX_KEY = None

    @abc.abstractmethod
    def key(self):
        return self.PREFIX_KEY

    @property
    def cached_data(self):
        return cache.get(self.key)

    def set_cached_data(self, data, timeout=None):
        cache.set(self.key, data, timeout=timeout)

    def clear(self):
        cache.delete(self.key)


class RequestCache(OsisCache):
    PREFIX_KEY = 'cache_filter'

    def __init__(self, user, path):
        self.user = user
        self.path = path

    @property
    def key(self):
        return "_".join([self.PREFIX_KEY, str(self.user.id), self.path])

    def save_get_parameters(self, request, parameters_to_exclude=None, timeout=None):
        parameters_to_exclude = parameters_to_exclude or []
        param_to_cache = {key: value for key, value in request.GET.lists() if key not in parameters_to_exclude}
        self.set_cached_data(param_to_cache, timeout=timeout)

    def restore_get_request(self, request, **default_values):
        cached_value = self.cached_data or default_values
        new_get_request = QueryDict(mutable=True)
        new_get_request.update({**request.GET.dict()})
        for key, value in cached_value.items():
            if type(value) == list:
                new_get_request.setlist(key, value)
            else:
                new_get_request[key] = value
        return new_get_request

    def get_single_value_cached(self, key: str):
        values_cached = self.get_values_list_cached(key)
        if not values_cached:
            return
        return values_cached[0]

    def get_values_list_cached(self, key: str) -> list:
        cached_data = self.cached_data or {}
        return cached_data.get(key) or []


class SearchParametersCache(OsisCache):
    PREFIX_KEY = "search_"

    def __init__(self, user, objects_class):
        self.user = user
        self.objects_class = objects_class

    @property
    def key(self):
        return "_".join([self.PREFIX_KEY, str(self.user.id), self.objects_class])


class ElementCache(OsisCache):
    PREFIX_KEY = 'select_element_{user}'

    class ElementCacheAction(Enum):
        COPY = "copy-action"
        CUT = "cut-action"

    def __init__(self, user_id: int):
        self.user_id = user_id

    @property
    def key(self):
        return self.PREFIX_KEY.format(user=self.user_id)

    def equals_element(self, element_code: str, element_year: int) -> bool:
        return (
            self.cached_data
            and self.cached_data['element_code'] == element_code
            and self.cached_data['element_year'] == element_year
        )

    def save_element_selected(
            self,
            element_code: str,
            element_year: int,
            path_to_detach: str = None,
            action: ElementCacheAction = ElementCacheAction.COPY
    ):
        data_to_cache = {
            'element_code': element_code,
            'element_year': element_year,
            'path_to_detach': path_to_detach,
            'action': action.value
        }
        self.set_cached_data(data_to_cache)


def cached_result(func):
    """
    Decorator used to cache the result returned by any function/property.
    Only works on functions/properties of an instance objects.
    """
    def f_cached(*args, **kwargs):
        self = args[0]
        cached_property_name = '__cached_' + func.__name__
        if hasattr(self, cached_property_name):
            result = getattr(self, cached_property_name, None)
        else:
            result = func(*args, **kwargs)
            setattr(self, cached_property_name, result)
        return result
    return f_cached
