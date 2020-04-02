############################################################################
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
############################################################################
from django.templatetags.static import static
from django.utils import six
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from base.models.enums.learning_unit_year_periodicity import BIENNIAL_EVEN, BIENNIAL_ODD, ANNUAL
from base.templatetags.education_group import register

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
            {value}
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


@register.filter
def pdf_tree_list(value):
    return mark_safe(list_formatter(value))


def walk_items(item_list):
    if item_list:
        item_iterator = iter(item_list)
        try:
            item = next(item_iterator)
            while True:
                try:
                    next_item = next(item_iterator)
                except StopIteration:
                    yield item, None
                    break
                if not isinstance(next_item, six.string_types):
                    try:
                        iter(next_item)
                    except TypeError:
                        pass
                    else:
                        yield item, next_item
                        item = next(item_iterator)
                        continue
                yield item, None
                item = next_item
        except StopIteration:
            pass
    else:
        return ""


def list_formatter(item_list, tabs=1, depth=None):
    output = []
    depth = depth if depth else 1
    for item, children in walk_items(item_list):
        sublist = ''
        padding = 2 * depth
        if children:
            sublist = '%s' % (
                list_formatter(children, tabs + 1, depth + 1))
        append_output(item, output, padding, sublist)
    return '\n'.join(output)


def append_output(item, output, padding, sublist):
    comment = CHILD_COMMENT.format(
        comment_value=item.verbose_comment
    ) if item and item.verbose_comment else ""

    if item.child_leaf:
        mandatory_picture = get_mandatory_picture(item)
        output.append(
            CHILD_LEAF.format(padding=padding,
                              icon_list_1=get_case_picture(item),
                              icon_list_2=mandatory_picture,
                              icon_list_3=get_status_picture(item),
                              icon_list_4=get_biennial_picture(item),
                              icon_list_5=get_prerequis_picture(item),
                              value=force_text(item.verbose),
                              comment=comment,
                              sublist=sublist,
                              an_1=check_block(item, 1),
                              an_2=check_block(item, 2),
                              an_3=check_block(item, 3),
                              an_4=check_block(item, 4),
                              an_5=check_block(item, 5),
                              an_6=check_block(item, 6),
                              )
        )
    else:
        constraint = BRANCH_CONSTRAINT.format(
            constraint_value=item.child_branch.verbose_constraint
        ) if item.child_branch.constraint_type else ""

        remark = BRANCH_REMARK.format(remark_value=item.child.verbose_remark) if item.child.verbose_remark else ""

        output.append(
            CHILD_BRANCH.format(padding=padding,
                                constraint=constraint,
                                icon_list_2=get_mandatory_picture(item),
                                value=force_text(item.verbose),
                                remark=remark,
                                comment=comment,
                                sublist=sublist
                                )
        )


def get_status_picture(item):
    return DELTA if not item.child_leaf.status else ""


def get_biennial_picture(item):
    if item.child_leaf.periodicity == BIENNIAL_EVEN:
        return BISANNUAL_EVEN
    elif item.child_leaf.periodicity == BIENNIAL_ODD:
        return BISANNUAL_ODD
    else:
        return ""


def get_mandatory_picture(item):
    return MANDATORY_PNG if item.is_mandatory else OPTIONAL_PNG


def get_prerequis_picture(item):
    return PREREQUIS if item.has_prerequisite else None


def get_case_picture(item):
    if item.child_leaf.status:
        if item.child_leaf.periodicity == ANNUAL:
            return VALIDATE_CASE_JPG
        elif item.child_leaf.periodicity == BIENNIAL_EVEN and item.child_leaf.academic_year.is_even:
            return VALIDATE_CASE_JPG
        elif item.child_leaf.periodicity == BIENNIAL_ODD and item.child_leaf.academic_year.is_odd:
            return VALIDATE_CASE_JPG
    return INVALIDATE_CASE_JPG


def check_block(item, value):
    return "X" if item.block and value == item.block else ""
