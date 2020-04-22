from django.db.models import Func


class ArrayConcat(Func):
    template = '%(expressions)s'
    arg_joiner = ' || '
