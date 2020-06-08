from django import template

register = template.Library()


@register.filter
def format_to_academic_year(year: int):
    """
    Format year (XXXX) into academic year format (XXXX-XX)
    """
    return u"%s-%s" % (year, str(year + 1)[-2:])
