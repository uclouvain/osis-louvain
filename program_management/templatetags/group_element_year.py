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
from django import template

from base.templatetags.common import ICONS
from osis_role.errors import get_permission_error

register = template.Library()


@register.inclusion_tag("blocks/button/action_template.html")
def action_with_permission(person, group, title, value, perm, url):
    has_perm = person.user.has_perm(perm, group.parent)

    return {
        'load_modal': has_perm,
        'title': title if has_perm else get_permission_error(person.user, perm),
        'disabled': '' if has_perm else 'disabled',
        'icon': ICONS[value],
        'url': url,
    }
