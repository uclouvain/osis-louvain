##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List
from collections import defaultdict
from django.db.models import QuerySet
from django.db.models.expressions import RawSQL
from openpyxl.styles import Color, Font

from base.business.learning_unit_xls import HEADER_TEACHERS, \
    learning_unit_titles_part_1, learning_unit_titles_part2, annotate_qs, get_data_part1, get_data_part2, \
    prepare_proposal_legend_ws_data, title_with_version_title, \
    acronym_with_version_label, BOLD_FONT, get_name_or_username, \
    WRAP_TEXT_ALIGNMENT, _get_col_letter, PROPOSAL_LINE_STYLES
from base.business.xls import _get_all_columns_reference
from base.models.learning_unit_year import SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS, LearningUnitYear, \
    LearningUnitYearQuerySet
from osis_common.document import xls_build
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from base.models.entity_version import EntityVersion
from base.models.academic_year import AcademicYear

XLS_FILENAME = _('LearningUnitsTrainingsList')
CELLS_WITH_BORDER_TOP = 'cells_with_border_top'
CELLS_TO_COLOR = 'cells_to_color'
XLS_DESCRIPTION = _('List of learning units with one line per training')
WORKSHEET_TITLE = _('Learning units training list')
WHITE_FONT = Font(color=Color('00FFFFFF'))
FIRST_TRAINING_COLUMN = 28
TOTAL_NB_OF_COLUMNS = 33
HEADER_PROGRAMS = [
    str(_('Gathering')),
    str(_('Training code')),
    str(_('Training title')),
    str(_('Training management entity')),
    str(_('Training management entity faculty')),
]
BLACK_FONT = Font(color=Color('00000000'))
REQUIREMENT_ENTITY_COL = 'F'
ALLOCATION_ENTITY_COL = 'J'
STYLED_CELLS = "styled_cells"


def create_xls_ue_utilizations_with_one_training_per_line(user, learning_units, filters):
    data = _prepare_xls_content(learning_units)
    working_sheets_data = data.get('working_sheets_data')

    parameters = _get_parameters(data, learning_units, _prepare_titles(), user)

    ws_data = xls_build.prepare_xls_parameters_list(working_sheets_data, parameters)

    ws_data.update(
        {
            xls_build.WORKSHEETS_DATA: [ws_data.get(xls_build.WORKSHEETS_DATA)[0], prepare_proposal_legend_ws_data()]
        }
    )

    return xls_build.generate_xls(ws_data, filters)


def _prepare_titles() -> List['str']:
    titles_part1 = learning_unit_titles_part_1(display_proposal=True)
    titles_part2 = learning_unit_titles_part2()
    titles_part2.extend(HEADER_PROGRAMS)
    titles_part1.extend(HEADER_TEACHERS)
    titles_part1.extend(titles_part2)
    return titles_part1


def _get_parameters(data: Dict, learning_units, titles_part1, user) -> dict:
    parameters = _get_parameters_configurable_list(learning_units, titles_part1, user)
    parameters.update(
        {
            xls_build.FONT_CELLS: data.get(STYLED_CELLS),
            xls_build.BORDER_CELLS: {xls_build.BORDER_TOP: data.get(CELLS_WITH_BORDER_TOP)},
            xls_build.FONT_ROWS: {BOLD_FONT: [0]},
        }
    )
    return parameters


def _prepare_xls_content(learning_unit_years: QuerySet) -> Dict:
    qs = annotate_qs(learning_unit_years)
    qs = qs.annotate(
        closest_trainings=RawSQL(SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS, ())
    ).prefetch_related('element')
    qs = LearningUnitYearQuerySet.annotate_entities_status(qs)
    lines = []
    cells_with_border_top = []
    styled_cells = defaultdict(list)
    for learning_unit_yr in qs:
        lu_data_part1 = get_data_part1(learning_unit_yr, is_external_ue_list=False)
        lu_data_part2 = get_data_part2(learning_unit_yr, with_attributions=True)

        if hasattr(learning_unit_yr, "element") and learning_unit_yr.element.children_elements.all():
            training_occurence = 1
            for group_element_year in learning_unit_yr.element.children_elements.all():
                if not learning_unit_yr.closest_trainings or group_element_year.parent_element.group_year is None:
                    break

                partial_acronym = group_element_year.parent_element.group_year.partial_acronym or ''
                credits = group_element_year.relative_credits \
                    if group_element_year.relative_credits \
                    else group_element_year.child_element.learning_unit_year.credits
                leaf_credits = "{0:.2f}".format(credits) if credits else '-'

                for training in learning_unit_yr.closest_trainings:
                    if training['gs_origin'] == group_element_year.pk:
                        training_data = _build_training_data_columns(
                            leaf_credits,
                            partial_acronym,
                            training,
                            learning_unit_yr.academic_year
                        )
                        if training_data:
                            lines.append(lu_data_part1 + lu_data_part2 + training_data)
                            styled_cells = _get_styled_cells(
                                styled_cells,
                                learning_unit_yr,
                                len(lines) + 1,
                                training_occurence
                            )
                            if training_occurence == 1:
                                cells_with_border_top.extend(_add_border_top(len(lines)+1))

                            training_occurence += 1
        else:
            lines.append(lu_data_part1 + lu_data_part2)
            cells_with_border_top.extend(_add_border_top(len(lines)+1))
            styled_cells = _get_styled_cells(styled_cells, learning_unit_yr, len(lines) + 1)

    return {
        'working_sheets_data': lines,
        CELLS_WITH_BORDER_TOP: cells_with_border_top,
        STYLED_CELLS: styled_cells
    }


def _build_training_data_columns(leaf_credits: str,
                                 partial_acronym: str,
                                 training: dict,
                                 an_academic_year: AcademicYear) -> List:
    data = list()
    data.append("{} ({})".format(partial_acronym, leaf_credits))
    data.append("{}".format(acronym_with_version_label(
        training['acronym'], training['transition_name'], training['version_name']))
    )
    data.append("{}".format(
        title_with_version_title(training['title_fr'], training['version_title_fr']))
    )
    management_entity = EntityVersion.objects.filter(
        Q(entity__id=training['management_entity'], start_date__lte=an_academic_year.end_date),
        Q(end_date__isnull=True) | Q(end_date__gt=an_academic_year.end_date)
    ).last()
    data.append(management_entity.acronym if management_entity else '-')
    data.append(_get_management_entity_faculty(management_entity, an_academic_year))
    return data


def _get_parameters_configurable_list(learning_units: List, titles: List, user) -> dict:
    parameters = {
        xls_build.DESCRIPTION: XLS_DESCRIPTION,
        xls_build.USER: get_name_or_username(user),
        xls_build.FILENAME: XLS_FILENAME,
        xls_build.HEADER_TITLES: titles,
        xls_build.WS_TITLE: WORKSHEET_TITLE,
        xls_build.ALIGN_CELLS: {
            WRAP_TEXT_ALIGNMENT: _get_wrapped_cells(
                learning_units,
                _get_col_letter(titles, HEADER_TEACHERS)
            )
        },
    }
    return parameters


def _get_wrapped_cells(learning_units: List, teachers_col_letter: List[str]) -> List:
    wrapped_styled_cells = []

    for idx, luy in enumerate(learning_units, start=2):
        if teachers_col_letter:
            for teacher_col_letter in teachers_col_letter:
                wrapped_styled_cells.append("{}{}".format(teacher_col_letter, idx))

    return wrapped_styled_cells


def _add_border_top(row: int) -> List['str']:
    return [
        "{}{}".format(letter, row) for letter in _get_all_columns_reference(TOTAL_NB_OF_COLUMNS)
    ]


def _get_styled_cells(
        styled_cells_to_update: Dict[Font, List],
        learning_unit_yr: LearningUnitYear,
        row_number: int,
        training_occurence: int = 1
) -> Dict[Font, List]:
    styled_cells = styled_cells_to_update.copy()
    font_training = BLACK_FONT
    font_ue = BLACK_FONT

    if training_occurence > 1:
        font_ue = WHITE_FONT
        if getattr(learning_unit_yr, "proposallearningunit", None):
            font_training = PROPOSAL_LINE_STYLES.get(learning_unit_yr.proposallearningunit.type).copy()
    else:
        if getattr(learning_unit_yr, "proposallearningunit", None):
            font_ue = PROPOSAL_LINE_STYLES.get(learning_unit_yr.proposallearningunit.type).copy()
            font_training = PROPOSAL_LINE_STYLES.get(learning_unit_yr.proposallearningunit.type).copy()
    font_requirement_entity = font_ue.copy()
    font_allocation_entity = font_ue.copy()

    if not learning_unit_yr.active_entity_requirement_version:
        font_requirement_entity.strikethrough = True

    if not learning_unit_yr.active_entity_allocation_version:
        font_allocation_entity.strikethrough = True

    ue_cols = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
        'W', 'X', 'Y', 'Z'
    ]
    for letter in _get_all_columns_reference(TOTAL_NB_OF_COLUMNS):
        cell_ref = "{}{}".format(letter, row_number)
        if letter == REQUIREMENT_ENTITY_COL:
            styled_cells[font_requirement_entity].append(cell_ref)
        elif letter == ALLOCATION_ENTITY_COL:
            styled_cells[font_allocation_entity].append(cell_ref)
        elif letter in ue_cols:
            styled_cells[font_ue].append(cell_ref)
        else:
            styled_cells[font_training].append(cell_ref)
    return styled_cells


def _get_management_entity_faculty(management_entity: EntityVersion, academic_year: AcademicYear) -> str:
    if management_entity:
        faculty_entity = management_entity.find_faculty_version(academic_year)
        return faculty_entity.acronym if faculty_entity else management_entity.acronym
    return '-'
