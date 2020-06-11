from datetime import datetime
from typing import Any, Tuple

from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter(is_safe=True)
def dates_from_to(obj: Any):
    """
    :param obj: Any object that contains fields 'start_date' and 'end_date'
    :return: a translated text formated like 'From 24/06/2020 to 25/06/2020'.
    """
    start_date, end_date = __get_start_end_date(obj)
    if start_date or end_date:
        return "{_from} {date_from} {_to} {date_to}".format(
            _from=_('From'),
            date_from=start_date.strftime("%d/%m/%Y") if start_date else _('undefined'),
            _to=_('to'),
            date_to=end_date.strftime("%d/%m/%Y") if end_date else _('undefined'),
        )
    return ""


@register.filter(is_safe=True)
def datetimes_at(dt: datetime):
    """
    :param dt: a datetime
    :return: a translated text formated like '24/06/2020 at 14h54'.
    """
    if dt:
        return "{date_format} {at} {hour}".format(
            date_format=dt.strftime("%d/%m/%Y") if dt else _('undefined'),
            at=_('at'),
            hour=dt.strftime("%H:%M") if dt else _('undefined'),
        )
    return ""


def __get_start_end_date(obj: Any):
    if isinstance(obj, dict):
        start_date = obj.get('start_date')
        end_date = obj.get('end_date')
    else:
        start_date = getattr(obj, 'start_date', None)
        end_date = getattr(obj, 'end_date', None)
    return start_date, end_date
