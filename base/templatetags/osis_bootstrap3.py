##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import defaultdict

from bootstrap3.templatetags import bootstrap3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def bootstrap_row(**kwargs):
    field_parameters_by_position = defaultdict(dict)
    for name, value in kwargs.items():
        position, field_parameter = extract_position_and_field_parameter(name)
        field_parameters_by_position[position][field_parameter] = value

    keys = sorted(field_parameters_by_position.keys())
    fields = [field_parameters_by_position[key] for key in keys
              if "field" in field_parameters_by_position[key] and field_parameters_by_position[key]["field"]]
    return mark_safe(_render_row(fields))


def extract_position_and_field_parameter(field_parameter):
    field_parameter, separator, position = field_parameter.rpartition("_")
    return int(position), field_parameter


def _render_row(fields):
    if not fields:
        return ""

    rendering = '<div class="form-group row">\n'

    for field in fields:
        rendering += "\t" + bootstrap3.bootstrap_field(**field) + "\n"

    rendering += '</div>'

    return rendering
