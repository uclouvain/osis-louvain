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
import datetime
import pickle
import time

from base.utils.cache import cache

CACHE_NOTIFICATIONS_TIMEOUT = 300  # seconds -> 5 min
NOTIFICATIONS_KEY = "notifications_unread_user_{}"
NOTIFICATIONS_TIMESTAMP = "notifications_last_read_user_{}"


def cache_queryset_function(function):
    def wrapper(user, *args, **kwargs):
        cache_key = make_notifications_cache_key(user)

        pickled_qs = cache.get(cache_key)
        if pickled_qs:
            return pickle.loads(pickled_qs)

        qs = function(user, *args, **kwargs)
        cache.set(cache_key, pickle.dumps(qs), CACHE_NOTIFICATIONS_TIMEOUT)
        return qs
    return wrapper


def invalidate_cache(function):
    def wrapper(user, *args, **kwargs):
        cache_key = make_notifications_cache_key(user)
        cache.delete(cache_key)
        return function(user, *args, **kwargs)
    return wrapper


def apply_function_if_data_not_in_cache(function):
    def wrapper(user, *args, **kwargs):
        cache_key = make_notifications_cache_key(user)
        if cache.get(cache_key) is not None:
            return None
        return function(user, *args, **kwargs)
    return wrapper


@cache_queryset_function
def get_user_notifications(user):
    return user.notifications.all().order_by("-unread")


def get_user_unread_notifications(user):
    return user.notifications.unread()


def get_user_read_notifications(user):
    return user.notifications.read()


@invalidate_cache
def mark_notifications_as_read(user):
    user.notifications.mark_all_as_read()


@invalidate_cache
def clear_user_notifications(user):
    user.notifications.all().delete()


def get_notifications_last_time_read_for_user(user):
    cache_key = make_notifications_timestamp_cache_key(user)
    timestamp_last_read = cache.get(cache_key)
    return datetime.datetime.fromtimestamp(float(timestamp_last_read)) if timestamp_last_read else None


def set_notifications_last_read_as_now_for_user(user):
    cache_key = make_notifications_timestamp_cache_key(user)
    cache.set(cache_key, str(time.time()), timeout=None)


def make_notifications_timestamp_cache_key(user):
    return NOTIFICATIONS_TIMESTAMP.format(user.pk)


def make_notifications_cache_key(user):
    return NOTIFICATIONS_KEY.format(user.pk)
