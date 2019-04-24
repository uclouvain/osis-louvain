#############################################################################
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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units.comparison import DEFAULT_VALUE_FOR_NONE
from base.business.utils.convert import volume_format
from base.models.enums.learning_unit_year_subtypes import PARTIM
from base.models.learning_unit_year import find_lt_learning_unit_year_with_different_acronym
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.models.utils.utils import get_verbose_field_value

register = template.Library()
DIFFERENCE_CSS = "style='color:#5CB85C;'"
CSS_PROPOSAL_VALUE = "proposal_value"
LABEL_VALUE_BEFORE_PROPOSAL = _('Value before proposal')


@register.filter
def academic_years(start_year, end_year):
    if start_year and end_year:
        str_start_year = ''
        str_end_year = ''
        if start_year:
            str_start_year = "{} {}-{}".format(_('From').title(), start_year, str(start_year + 1)[-2:])
        if end_year:
            str_end_year = "{} {}-{}".format(_('to'), end_year, str(end_year + 1)[-2:])
        return "{} {}".format(str_start_year, str_end_year)
    else:
        if start_year and not end_year:
            return "{} {}-{} ({})".format(_('From'), start_year, str(start_year + 1)[-2:], _('no planned end'))
        else:
            return "-"


@register.filter
def academic_year(year):
    if year:
        return "{}-{}".format(year, str(year + 1)[-2:])
    return "-"


@register.filter
def get_difference_css(differences, parameter, default_if_none=""):
    if parameter in differences:
        value = differences[parameter]
        return mark_safe(
            ' data-toggle=tooltip title="{} : {}" class="{}" '.format(
                LABEL_VALUE_BEFORE_PROPOSAL,
                value or default_if_none,
                CSS_PROPOSAL_VALUE
            )
        )
    return None


@register.filter
def has_proposal(luy):
    return ProposalLearningUnit.objects.filter(learning_unit_year=luy).exists()


# TODO Use inclusion tag instead
@register.simple_tag(takes_context=True)
def dl_tooltip(context, instance, key, **kwargs):
    title = kwargs.get('title', '')
    label_text = _(str(kwargs.get('label_text', '')))
    url = kwargs.get('url', '')
    default_if_none = kwargs.get('default_if_none', '')
    value = kwargs.get('value', '')
    inherited = kwargs.get('inherited', '')
    not_annualized = kwargs.get('not_annualized', '')
    differences = context['differences']

    if not label_text:
        label_text = instance._meta.get_field(key).verbose_name.capitalize()

    if not value:
        value = get_verbose_field_value(instance, key)

    difference = get_difference_css(differences, key, default_if_none) or 'title="{}"'.format(_(title))

    if url:
        value = "<a href='{url}'>{value}</a>".format(value=_(str(value)), url=url)

    if inherited == PARTIM:
        label_text = get_style_of_label_text(label_text, "color:grey",
                                             "The value of this attribute is inherited from the parent UE")
        value = get_style_of_value("color:grey", "The value of this attribute is inherited from the parent UE", value)

    if not_annualized:
        label_text = get_style_of_label_text(label_text, "font-style:italic",
                                             "The value of this attribute is not annualized")
        value = get_style_of_value("font-style:italic",
                                   "The value of this attribute is not annualized",
                                   value if value else default_if_none
                                   )

    html_id = "id='id_{}'".format(key.lower())

    return mark_safe("<dl><dt {difference}>{label_text}</dt><dd {difference} {id}>{value}</dd></dl>".format(
        difference=difference, id=html_id, label_text=label_text, value=value or ''))


def get_style_of_value(style, title, value):
    value = "<p style='{style}' title='{title}'>{value}</p>".format(style=style, title=_(title), value=value)
    return value


def get_style_of_label_text(label_text, style, title):
    label_text = '<label style="{style}" title="{inherited_title}">{label_text}</label>' \
        .format(style=style, inherited_title=_(title), label_text=label_text)
    return label_text


@register.filter
def get_previous_acronym(luy):
    if has_proposal(luy):
        return _get_acronym_from_proposal(luy)
    else:
        previous_luy = find_lt_learning_unit_year_with_different_acronym(luy)
        return previous_luy.acronym if previous_luy else None


def _get_acronym_from_proposal(luy):
    proposal = ProposalLearningUnit.objects \
        .filter(learning_unit_year=luy) \
        .order_by('-learning_unit_year__academic_year__year').first()
    if proposal and proposal.initial_data and proposal.initial_data.get('learning_unit_year'):
        return proposal.initial_data['learning_unit_year']['acronym']
    return None


@register.simple_tag
def value_label(values_dict, key, sub_key, key_comp):
    data = values_dict.get(key)
    if data:
        val = data.get(sub_key)
        return _get_label(data, key_comp, val)
    return DEFAULT_VALUE_FOR_NONE


def _get_label(data, key_comp, val):
    if val != data.get(key_comp):
        return mark_safe("<label {}>{}</label>"
                         .format(DIFFERENCE_CSS, DEFAULT_VALUE_FOR_NONE if val is None else val))
    else:
        return mark_safe("{}".format(DEFAULT_VALUE_FOR_NONE if val is None else val))


@register.simple_tag
def changed_label(value, other=None):
    if value != other and other:
        return mark_safe(
            "<td><label {}>{}</label></td>".format(DIFFERENCE_CSS, DEFAULT_VALUE_FOR_NONE if value is None else value))
    else:
        return mark_safe("<td><label>{}</label></td>".format(DEFAULT_VALUE_FOR_NONE if value is None else value))


@register.simple_tag(takes_context=True)
def dl_component_tooltip(context, key, **kwargs):
    title = kwargs.get('title', '')
    default_if_none = kwargs.get('default_if_none', '')
    value = kwargs.get('value', '')
    id = kwargs.get('id', '')

    volumes = {}
    components_initial_data = context.get('differences', {}).get('components_initial_data', {})
    if components_initial_data != {}:
        for rec in components_initial_data.get('components', {}):
            if rec.get('learning_component_year').get('id') == id:
                volumes = rec.get('volumes')
                break

        difference = get_component_volume_css(volumes, key, default_if_none, value) or 'title="{}"'.format(_(title))
        value = get_style_of_value("", "", volume_format(value))
        html_id = "id='id_{}'".format(key.lower())

        return mark_safe("<dl><dd {difference} {id}>{value}</dd></dl>".format(
            difference=difference, id=html_id, value=str(value)))
    return volume_format(value) if value else default_if_none


@register.filter
def get_component_volume_css(values, parameter, default_if_none="", value=None):
    if parameter in values and values[parameter] != value:
        return mark_safe(
            " data-toggle=tooltip title='{} : {}' class='{}' ".format(
                LABEL_VALUE_BEFORE_PROPOSAL,
                volume_format(values[parameter]) or default_if_none,
                CSS_PROPOSAL_VALUE
            )
        )
    return default_if_none


@register.simple_tag(takes_context=True)
def th_tooltip(context, key, **kwargs):
    value = kwargs.get('value', '')
    differences = context.get('differences')
    default_if_none = '-'

    if differences:
        difference = get_difference_css(differences, key, default_if_none)
    else:
        difference = ''

    return mark_safe("<span {difference}>{value}</span>".format(
        difference=difference, value=_(str(value))))
