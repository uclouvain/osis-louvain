from functools import wraps

from django.conf import settings


def predicate_cache(cache_key_fn=None):
    def predicate_decorator(func):
        @wraps(func)
        def wrapped_function(self, user_obj, *args, **kwargs):
            if not settings.PERMISSION_CACHE_ENABLED:
                return func(self, user_obj, *args, **kwargs)
            predicate_cache_key = _build_cache_key(func, cache_key_fn, *args, **kwargs)
            try:
                cached_result = get_cache_predicate_result(user_obj, predicate_cache_key)
            except CachePredicateResultNotFound:
                cached_result = func(self, user_obj, *args, **kwargs)
                set_cache_predicate_result(user_obj, predicate_cache_key, cached_result)
            return cached_result
        return wrapped_function
    return predicate_decorator


def get_cache_predicate_result(user_obj, predicate_cache_key):
    if hasattr(user_obj, '_cache_predicates') and predicate_cache_key in user_obj._cache_predicates:
        return user_obj._cache_predicates[predicate_cache_key]
    raise CachePredicateResultNotFound


def set_cache_predicate_result(user_obj, predicate_cache_key, result):
    if not hasattr(user_obj, '_cache_predicates'):
        setattr(user_obj, '_cache_predicates', {})
    user_obj._cache_predicates[predicate_cache_key] = result


def _build_cache_key(func, cache_key_fn, *args, **kwargs):
    args_types = "_".join(type(arg).__name__ for arg in args)
    return "_".join(filter(None, [func.__name__, args_types, str(cache_key_fn(*args, **kwargs))]))


class CachePredicateResultNotFound(Exception):
    pass
