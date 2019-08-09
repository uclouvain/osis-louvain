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
import functools

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.models import learning_unit_year

register = template.Library()


@register.simple_tag
def prerequisite_string(prerequisite, learning_unit_year_parent):
    display_method = functools.partial(_get_acronym_as_href, learning_unit_year_parent)
    return mark_safe(prerequisite._get_acronyms_string(display_method=display_method)) if prerequisite else '-'


def _get_acronym_as_href(learning_unit_year_parent, prerequisite_item, academic_yr):
    luy = learning_unit_year.search(
        academic_year_id=academic_yr.id,
        learning_unit=prerequisite_item.learning_unit,
    ).first()

    if luy:
        return "<a href='/learning_units/{}/' title=\"{}\">{}</a>".format(
            luy.id,
            _get_acronym_tooltip(luy, learning_unit_year_parent),
            prerequisite_item.learning_unit.acronym
        )
    return ''


def _get_acronym_tooltip(luy, learning_unit_year_parent):
    parent = learning_unit_year_parent.get(luy.id)
    relative_credits = str(parent.relative_credits) if parent else "-"
    return "{}\n{} : {} / {}".format(
        luy.complete_title,
        _('Cred. rel./abs.'),
        relative_credits,
        luy.credits.normalize()
    )
