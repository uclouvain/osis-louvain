import rules

from osis_role.errors import predicate_failed_msg


def always_deny(message=''):
    @rules.predicate(bind=True)
    @predicate_failed_msg(message)
    def always_deny_fn(*args, **kwargs):
        return False
    return always_deny_fn
