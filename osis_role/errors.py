from functools import wraps


def clear_permission_error(user_obj, perm):
    set_permission_error(user_obj, perm, error=None)


def get_permission_error(user_obj, perm):
    if hasattr(user_obj, '_cached_error_perms') and perm in user_obj._cached_error_perms:
        return user_obj._cached_error_perms[perm]
    return None


def set_permission_error(user_obj, perm, error):
    if not hasattr(user_obj, '_cached_error_perms'):
        setattr(user_obj, '_cached_error_perms', {})
    user_obj._cached_error_perms[perm] = error


def predicate_failed_msg(message=None):
    def predicate_decorator(func):
        @wraps(func)
        def wrapped_function(self, user_obj, *args, **kwargs):
            result = func(self, user_obj, *args, **kwargs)
            if result is False:
                perm_name = self.context['perm_name']
                set_permission_error(user_obj, perm_name, message)
            return result
        return wrapped_function
    return predicate_decorator
