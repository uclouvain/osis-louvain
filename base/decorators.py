##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import logging

from django.conf import settings
from django.core.cache import cache
from functools import wraps

CACHE_FILTER_TIMEOUT = None
PREFIX_CACHE_KEY = 'cache_filter'

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def cache_filter(param_list=None):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            try:
                if request.GET:
                    _save_filter_to_cache(request, param_list)
                _restore_filter_from_cache(request, param_list)
            except Exception:
                logger.exception('An error occured with cache system')
            return func(request, *args, **kwargs)
        return inner
    return decorator


def _save_filter_to_cache(request, param_list):
    param_to_cache = {key: value for key, value in request.GET.items() if key in param_list} if param_list \
                     else request.GET
    key = _get_filter_key(request)
    cache.set(key, param_to_cache, timeout=CACHE_FILTER_TIMEOUT)


def _restore_filter_from_cache(request, param_list):
    cached_value = _get_from_cache(request)
    if cached_value:
        request.GET = {key: value for key, value in cached_value.items() if key in param_list} if param_list \
                      else cached_value


def _get_from_cache(request):
    key = _get_filter_key(request)
    return cache.get(key)


def _get_filter_key(request):
    user = request.user
    path = request.path
    return "_".join([PREFIX_CACHE_KEY, str(user.id), path])
