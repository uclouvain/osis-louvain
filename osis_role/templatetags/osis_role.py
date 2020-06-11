from django import template
from rules.templatetags import rules

from osis_role import errors

register = template.Library()


@register.inclusion_tag('osis_role/templatetags/a_template.html')
def a_tag_has_perm(url, text, perm, user, obj=None):
    context = {"text": text, "url": url}
    has_perm = user.has_perm(perm, obj)
    if not has_perm:
        context.update({
            "url": "#",
            "class_a": "disabled",
            "error_msg": errors.get_permission_error(user, perm) or ""
        })
    return context


@register.inclusion_tag('osis_role/templatetags/a_template.html')
def a_tag_modal_has_perm(url, text, perm, user, obj=None):
    return {
        "class_a": "trigger_modal",
        "load_modal": True,
        **a_tag_has_perm(url, text, perm, user, obj),
    }


@register.simple_tag
def has_perm(perm, user, obj=None):
    return rules.has_perm(perm, user, obj)


@register.simple_tag
def has_module_perms(user, app_label):
    return user.has_module_perms(app_label)
