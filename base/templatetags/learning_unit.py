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
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.business.learning_units.comparison import DEFAULT_VALUE_FOR_NONE
from base.models.enums.learning_unit_year_subtypes import PARTIM
from base.models.learning_unit_year import find_lt_learning_unit_year_with_different_acronym, \
    find_gt_learning_unit_year_with_different_acronym
from base.models.proposal_learning_unit import ProposalLearningUnit, is_in_proposal_of_transformation
from base.models.utils.utils import get_verbose_field_value
from osis_common.utils.numbers import normalize_fraction

register = template.Library()
DIFFERENCE_CSS = "style='color:#5CB85C;'"
CSS_PROPOSAL_VALUE = "proposal_value"
LABEL_VALUE_BEFORE_PROPOSAL = _('Value before proposal')
EXTERNAL_CREDIT_TOOLTIP = _(
    'If the partner university does not use ECTS credit units, '
    'enter below the number of credit units according to the local system.'
)
GREY_COLOR = "color-grey"
ITALIC_FONT = "font-italic"


@register.filter
def academic_years(start_year, end_year):
    if start_year and end_year:
        str_start_year = ''
        str_end_year = ''
        if start_year:
            str_start_year = "{} {}-{}".format(_('From').title(), start_year.year, str(start_year.year + 1)[-2:])
        if end_year:
            str_end_year = "{} {}-{}".format(_('to'), end_year.year, str(end_year.year + 1)[-2:])
        return "{} {}".format(str_start_year, str_end_year)
    else:
        if start_year and not end_year:
            return "{} {}-{} ({})".format(_('From'), start_year.year,
                                          str(start_year.year + 1)[-2:],
                                          _('no planned end'))
        else:
            return "-"


@register.filter
def academic_year(academic_year):
    if academic_year:
        return "{}-{}".format(academic_year.year, str(academic_year.year + 1)[-2:])
    return "-"


@register.filter
def get_difference_css(differences, parameter, default_if_none=""):
    if parameter in differences:
        value = differences[parameter]
        return mark_safe(
            ' data-toggle=tooltip title="{} : {}" class="{}" '.format(
                LABEL_VALUE_BEFORE_PROPOSAL,
                normalize_fraction(Decimal(value)) if parameter == "credits" and differences[parameter] != '-'
                else value or default_if_none,
                CSS_PROPOSAL_VALUE
            )
        )
    return None


@register.filter
def has_proposal(luy):
    return ProposalLearningUnit.objects.filter(learning_unit_year=luy).exists()


@register.inclusion_tag("blocks/dl/dl_tooltip.html", takes_context=True)
def dl_tooltip(context, instance, key, **kwargs):
    title = kwargs.get('title', '')
    label_text = kwargs.get('label_text', '')
    url = kwargs.get('url', '')
    default_if_none = kwargs.get('default_if_none', '')
    value = kwargs.get('value')
    inherited = kwargs.get('inherited', '')
    not_annualized = kwargs.get('not_annualized', '')
    differences = context['differences']
    common_title = kwargs.get('common_title')
    specific_title = kwargs.get('specific_title')

    value_style_class = GREY_COLOR if inherited == PARTIM else ''

    if not label_text:
        label_text = instance._meta.get_field(key).verbose_name.capitalize()

    if not value:
        value = get_verbose_field_value(instance, key)

    value = normalize_fraction(value) if isinstance(value, Decimal) else value

    difference = get_difference_css(differences, key, default_if_none) or 'title="{}"'.format(
        EXTERNAL_CREDIT_TOOLTIP if key == 'external_credits' else _(title)
    )

    if url:
        value = "<a href='{url}'>{value}</a>".format(value=value or '', url=url)

    if inherited == PARTIM and not common_title:
        label_text = get_style_of_label_text(
            label_text, GREY_COLOR, "The value of this attribute is inherited from the parent UE"
        )
        value = get_style_of_value(GREY_COLOR, "The value of this attribute is inherited from the parent UE", value)

    if not_annualized:
        label_text = get_style_of_label_text(label_text, ITALIC_FONT, "The value of this attribute is not annualized")
        value = get_style_of_value(
            ITALIC_FONT,  "The value of this attribute is not annualized", value, default_if_none
        )

    if common_title or specific_title:
        is_common = common_title is True
        style_class, tooltip = _get_title_tooltip(is_common, inherited)
        label_text = get_style_of_label_text(label_text, style_class, tooltip)
        value = get_style_of_value(value_style_class, '', value, default_if_none)

    return {
        'difference': difference,
        'id': key.lower(),
        'label_text': label_text,
        'value': value or '-'
    }


def _get_title_tooltip(is_common, inherited):
    if is_common:
        label_style_class = " ".join([ITALIC_FONT, GREY_COLOR]) if inherited == PARTIM else ITALIC_FONT
        label_tooltip = _("Part of the title which is common to the complete EU, to its partims and to its classes")
        return label_style_class, label_tooltip
    return ITALIC_FONT, ''


def get_style_of_value(style_class, title, value, default_if_none=DEFAULT_VALUE_FOR_NONE):
    value = "<p class='{style_class}' title='{title}'>{value}</p>".format(
        style_class=style_class, title=_(title), value=value or default_if_none
    )
    return value


def get_style_of_label_text(label_text, style_class, title):
    label_text = '<label class="{style_class}" title="{inherited_title}">{label_text}</label>'.format(
        style_class=style_class, inherited_title=_(title), label_text=label_text
    )
    return label_text


@register.filter
def get_previous_acronym(luy):
    if has_proposal(luy) and is_in_proposal_of_transformation(luy):
        return _get_acronym_from_proposal(luy)
    else:
        previous_luy = find_lt_learning_unit_year_with_different_acronym(luy)
        return previous_luy and previous_luy.acronym


@register.filter
def get_next_acronym(luy):
    next_luy = find_gt_learning_unit_year_with_different_acronym(luy)
    return next_luy and next_luy.acronym


def _get_acronym_from_proposal(luy):
    proposal = ProposalLearningUnit.objects.filter(
        learning_unit_year=luy
    ).order_by('-learning_unit_year__academic_year__year').first()
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
        return mark_safe("<label {}>{}</label>".format(
            DIFFERENCE_CSS, DEFAULT_VALUE_FOR_NONE if val is None else val
        ))
    else:
        return mark_safe("{}".format(DEFAULT_VALUE_FOR_NONE if val is None else val))


@register.simple_tag
def changed_label(value, other=None):
    if str(value) != str(other) and other:
        return mark_safe("<td><label {}>{}</label></td>".format(
            DIFFERENCE_CSS, DEFAULT_VALUE_FOR_NONE if value is None else value
        ))
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
        value = get_style_of_value("", "", normalize_fraction(value))
        html_id = "id='id_{}'".format(key.lower())

        return mark_safe("<dl><dd {difference} {id}>{value}</dd></dl>".format(
            difference=difference, id=html_id, value=str(value)
        ))
    return normalize_fraction(value) if value else default_if_none


@register.filter
def get_component_volume_css(values, parameter, default_if_none="", value=None):
    if parameter in values and values[parameter] != value:
        return mark_safe(" data-toggle=tooltip title='{} : {}' class='{}' ".format(
                LABEL_VALUE_BEFORE_PROPOSAL,
                normalize_fraction(values[parameter]) or default_if_none,
                CSS_PROPOSAL_VALUE
        ))
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
        difference=difference, value=_(str(value))
    ))
