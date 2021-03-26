############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
from decimal import Decimal
from typing import List

from django.templatetags.static import static
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.templatetags.education_group import register
from program_management import formatter
from program_management.ddd.business_types import *

# TODO :: Remove this file and move the code into a Serializer

OPTIONAL_PNG = static('img/education_group_year/optional.png')
MANDATORY_PNG = static('img/education_group_year/mandatory.png')
VALIDATE_CASE_JPG = static('img/education_group_year/validate_case.jpg')
INVALIDATE_CASE_JPG = static('img/education_group_year/invalidate_case.png')
DELTA = static('img/education_group_year/delta.png')
BISANNUAL_EVEN = static('img/education_group_year/bisannual_even.png')
BISANNUAL_ODD = static('img/education_group_year/bisannual_odd.png')
PREREQUIS = static('img/education_group_year/prerequis.gif')
CHILD_BRANCH = """\
<tr>
    <td style="padding-left:{padding}em;">
        {constraint}
        <div style="word-break: keep-all;">
            <img src="{icon_list_2}" height="10" width="10">
            {value} <br>
            {remark}
            {comment}
            {sublist}
        </div>
    </td>
</tr>
"""
CHILD_LEAF = """\
<tr>
    <td style="padding-left:{padding}em;">
        <div style="word-break: keep-all;">
            <img src="{icon_list_1}" height="14" width="17">
            <img src="{icon_list_2}" height="10" width="10">
            <img src="{icon_list_5}" height="10" width="10">
            {value}
            <img src="{icon_list_3}" height="10" width="10">
            <img src="{icon_list_4}" height="10" width="10">
            <br>
            {comment}
            {sublist}
        </div>
    </td>
    <td style="text-align: center;">{an_1}</td>
    <td style="text-align: center;">{an_2}</td>
    <td style="text-align: center;">{an_3}</td>
    <td style="text-align: center;">{an_4}</td>
    <td style="text-align: center;">{an_5}</td>
    <td style="text-align: center;">{an_6}</td>
</tr>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
BRANCH_REMARK = """\
        <div style="word-break: keep-all;margin-left: 14px;">
            {remark_value}
        </div>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
CHILD_COMMENT = """\
        <div style="word-break: keep-all;margin-left: 32px;">
            ({comment_value})
        </div>
"""

# margin-left is there to align the value with the remark.
# We use 14px which is the size of the image before the value
BRANCH_CONSTRAINT = """\
        <div style="font-style: italic;">
            {constraint_value}
        </div>
"""


@register.filter  # TODO :: Remove this tag and move the code into a Serializer
def pdf_tree_list(tree: 'ProgramTree'):
    return mark_safe(list_formatter(tree, tree.root_node.children))


def list_formatter(tree: 'ProgramTree', links_under_root: List['Link'], tabs=1, depth=None):
    output = []
    depth = depth if depth else 1
    for link in links_under_root:
        sublist = ''
        padding = 2 * depth
        if link.child.children:
            sublist = '%s' % (
                list_formatter(tree, link.child.children, tabs + 1, depth + 1))
        append_output(tree, link, output, padding, sublist)
    return '\n'.join(output)


def append_output(tree: 'ProgramTree', link: 'Link', output, padding, sublist):
    comment = _get_verbose_comment(link)
    if link.is_link_with_learning_unit():
        mandatory_picture = get_mandatory_picture(link)
        output.append(
            CHILD_LEAF.format(padding=padding,
                              icon_list_1=get_case_picture(link.child),
                              icon_list_2=mandatory_picture,
                              icon_list_3=get_status_picture(link.child),
                              icon_list_4=get_biennial_picture(link.child),
                              icon_list_5=get_prerequis_picture(tree, link.child),
                              value=force_text(get_verbose_link(link)),
                              comment=comment,
                              sublist=sublist,
                              an_1=check_block(link, 1),
                              an_2=check_block(link, 2),
                              an_3=check_block(link, 3),
                              an_4=check_block(link, 4),
                              an_5=check_block(link, 5),
                              an_6=check_block(link, 6),
                              )
        )
    else:
        constraint = BRANCH_CONSTRAINT.format(
            constraint_value=get_verbose_constraint(link.child)
        ) if link.child.constraint_type else ""

        output.append(
            CHILD_BRANCH.format(padding=padding,
                                constraint=constraint,
                                icon_list_2=get_mandatory_picture(link),
                                value=force_text(get_verbose_link(link)),
                                remark=get_verbose_remark(link.child),
                                comment=comment,
                                sublist=sublist
                                )
        )


def _get_verbose_comment(link: 'Link'):
    comment_from_lang = link.comment
    if link.comment_english and translation.get_language() == LANGUAGE_CODE_EN:
        comment_from_lang = link.comment_english
    return CHILD_COMMENT.format(
        comment_value=comment_from_lang
    ) if comment_from_lang else ""


def get_verbose_remark(node: 'NodeGroupYear'):
    remark = node.remark_fr or ""
    if node.remark_en and translation.get_language() == LANGUAGE_CODE_EN:
        remark = node.remark_en
    return remark


def get_verbose_constraint(node: 'NodeGroupYear'):
    msg = "from %(min)s to %(max)s credits among" \
        if node.constraint_type == ConstraintTypeEnum.CREDITS else "from %(min)s to %(max)s among"
    return _(msg) % {
        "min": node.min_constraint if node.min_constraint else "",
        "max": node.max_constraint if node.max_constraint else ""
    }


def get_verbose_title_group(node: 'NodeGroupYear'):
    if node.is_finality():
        return format_complete_title_label(node, node.offer_partial_title_en, node.offer_partial_title_fr)
    if node.is_option():
        return format_complete_title_label(node, node.offer_title_en, node.offer_title_fr)
    else:
        return node.group_title_en \
            if node.group_title_en and translation.get_language() == LANGUAGE_CODE_EN else node.group_title_fr


def format_complete_title_label(node, title_en, title_fr):
    version_complete_label = formatter.format_version_complete_name(node, translation.get_language())
    if title_en and translation.get_language() == LANGUAGE_CODE_EN:
        return "{}{}".format(title_en, version_complete_label)
    else:
        return "{}{}".format(title_fr, version_complete_label)


def get_verbose_credits(link: 'Link'):
    if link.relative_credits or link.child.credits:
        return "{} ({} {})".format(
            get_verbose_title_group(link.child),
            link.relative_credits or link.child.credits or 0, _("credits")  # FIXME :: Duplicated line
        )
    else:
        return "{}".format(get_verbose_title_group(link.child))


def get_verbose_title_ue(node: 'NodeLearningUnitYear'):
    verbose_title_fr = node.full_title_fr
    verbose_title_en = node.full_title_en
    if verbose_title_en and translation.get_language() == LANGUAGE_CODE_EN:
        return verbose_title_en
    return verbose_title_fr


def get_verbose_link(link: 'Link'):
    if link.is_link_with_group():
        return get_verbose_credits(link)
    elif link.is_link_with_learning_unit():
        return "{} {} [{}] ({} {})".format(
            link.child.code,
            get_verbose_title_ue(link.child),
            get_volume_total_verbose(link.child),
            link.relative_credits or link.child.credits or 0, _("credits")  # FIXME :: Duplicated line
        )


def get_volume_total_verbose(node: 'NodeLearningUnitYear'):
    return "%(total_lecturing)gh + %(total_practical)gh" % {
        "total_lecturing": node.volume_total_lecturing or Decimal(0.0),
        "total_practical": node.volume_total_practical or Decimal(0.0)
    }


def get_status_picture(node: 'NodeLearningUnitYear'):
    return DELTA if not node.status else ""


def get_biennial_picture(node: 'NodeLearningUnitYear'):
    if node.periodicity == PeriodicityEnum.BIENNIAL_EVEN:
        return BISANNUAL_EVEN
    elif node.periodicity == PeriodicityEnum.BIENNIAL_ODD:
        return BISANNUAL_ODD
    else:
        return ""


def get_mandatory_picture(link: 'Link'):
    return MANDATORY_PNG if link.is_mandatory else OPTIONAL_PNG


def get_prerequis_picture(tree: 'ProgramTree', node: 'NodeLearningUnitYear'):
    return PREREQUIS if tree.has_prerequisites(node) else None


def get_case_picture(node: 'NodeLearningUnitYear'):
    if node.status:
        if node.periodicity == PeriodicityEnum.ANNUAL:
            return VALIDATE_CASE_JPG
        elif node.periodicity == PeriodicityEnum.BIENNIAL_EVEN and node.academic_year.is_even:
            return VALIDATE_CASE_JPG
        elif node.periodicity == PeriodicityEnum.BIENNIAL_ODD and node.academic_year.is_odd:
            return VALIDATE_CASE_JPG
    return INVALIDATE_CASE_JPG


def check_block(item, value):
    return "X" if item.block and str(value) in str(item.block) else ""
