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
from collections import defaultdict

from django.db.models import Subquery, OuterRef
from django.template.defaultfilters import yesno
from django.utils.translation import gettext_lazy as _
from openpyxl.styles import Alignment, Style, PatternFill, Color, Font
from openpyxl.utils import get_column_letter

from attribution.business import attribution_charge_new
from attribution.models.enums.function import Functions
from base import models as mdl_base
from base.business.learning_unit import learning_unit_titles_part2, XLS_DESCRIPTION, XLS_FILENAME, \
    WORKSHEET_TITLE
from base.business.xls import get_name_or_username
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.proposal_type import ProposalType
from base.models.learning_component_year import LearningComponentYear
from osis_common.document import xls_build

TRANSFORMATION_AND_MODIFICATION_COLOR = Color('808000')
TRANSFORMATION_COLOR = Color('ff6600')
SUPPRESSION_COLOR = Color('ff0000')
MODIFICATION_COLOR = Color('0000ff')
CREATION_COLOR = Color('008000')
DEFAULT_LEGEND_STYLES = {
    Style(fill=PatternFill(patternType='solid', fgColor=CREATION_COLOR)): ['A2'],
    Style(fill=PatternFill(patternType='solid', fgColor=MODIFICATION_COLOR)): ['A3'],
    Style(fill=PatternFill(patternType='solid', fgColor=SUPPRESSION_COLOR)): ['A4'],
    Style(fill=PatternFill(patternType='solid', fgColor=TRANSFORMATION_COLOR)): ['A5'],
    Style(fill=PatternFill(patternType='solid', fgColor=TRANSFORMATION_AND_MODIFICATION_COLOR)): ['A6'],
}
SPACES = '  '
HEADER_TEACHERS = _('List of teachers')
HEADER_PROGRAMS = _('Programs')
PROPOSAL_LINE_STYLES = {
    ProposalType.CREATION.name: Style(font=Font(color=CREATION_COLOR), ),
    ProposalType.MODIFICATION.name: Style(font=Font(color=MODIFICATION_COLOR), ),
    ProposalType.SUPPRESSION.name: Style(font=Font(color=SUPPRESSION_COLOR), ),
    ProposalType.TRANSFORMATION.name: Style(font=Font(color=TRANSFORMATION_COLOR), ),
    ProposalType.TRANSFORMATION_AND_MODIFICATION.name: Style(font=Font(color=TRANSFORMATION_AND_MODIFICATION_COLOR), ),
}
WRAP_TEXT_STYLE = Style(alignment=Alignment(wrapText=True, vertical="top"), )
WITH_ATTRIBUTIONS = 'with_attributions'
WITH_GRP = 'with_grp'


def learning_unit_titles_part1():
    return [
        str(_('Code')),
        str(_('Ac yr.')),
        str(_('Title')),
        str(_('Type')),
        str(_('Subtype')),
        "{} ({})".format(_('Req. Entity'), _('fac. level')),
        str(_('Proposal type')),
        str(_('Proposal status')),
        str(_('Credits')),
        str(_('Alloc. Ent.')),
        str(_('Title in English')),
    ]


def prepare_xls_content(learning_unit_years, with_grp=False, with_attributions=False):
    qs = annotate_qs(learning_unit_years)

    return [
        extract_xls_data_from_learning_unit(lu, with_grp, with_attributions) for lu in qs
    ]


def annotate_qs(learning_unit_years):
    """ Fetch directly in the queryset all volumes data."""

    subquery_component = LearningComponentYear.objects.filter(
        learning_unit_year__in=OuterRef('pk')
    )
    subquery_component_pm = subquery_component.filter(
        type=LECTURING
    )
    subquery_component_pp = subquery_component.filter(
        type=PRACTICAL_EXERCISES
    )

    return learning_unit_years.annotate(
        pm_vol_q1=Subquery(subquery_component_pm.values('hourly_volume_partial_q1')[:1]),
        pm_vol_q2=Subquery(subquery_component_pm.values('hourly_volume_partial_q2')[:1]),
        pm_vol_tot=Subquery(subquery_component_pm.values('hourly_volume_total_annual')[:1]),
        pm_classes=Subquery(subquery_component_pm.values('planned_classes')[:1]),
        pp_vol_q1=Subquery(subquery_component_pp.values('hourly_volume_partial_q1')[:1]),
        pp_vol_q2=Subquery(subquery_component_pp.values('hourly_volume_partial_q2')[:1]),
        pp_vol_tot=Subquery(subquery_component_pp.values('hourly_volume_total_annual')[:1]),
        pp_classes=Subquery(subquery_component_pp.values('planned_classes')[:1])
    )


def extract_xls_data_from_learning_unit(learning_unit_yr, with_grp, with_attributions):
    lu_data_part1 = _get_data_part1(learning_unit_yr)
    lu_data_part2 = _get_data_part2(learning_unit_yr, with_attributions)

    if with_grp:
        lu_data_part2.append(_add_training_data(learning_unit_yr))
    lu_data_part1.extend(lu_data_part2)
    return lu_data_part1


def create_xls_with_parameters(user, learning_units, filters, extra_configuration):
    with_grp = extra_configuration.get(WITH_GRP)
    with_attributions = extra_configuration.get(WITH_ATTRIBUTIONS)
    titles_part1 = learning_unit_titles_part1()
    titles_part2 = learning_unit_titles_part2()

    if with_grp:
        titles_part2.append(str(HEADER_PROGRAMS))

    if with_attributions:
        titles_part1.append(str(HEADER_TEACHERS))

    working_sheets_data = prepare_xls_content(learning_units, with_grp, with_attributions)

    titles_part1.extend(titles_part2)

    ws_data = xls_build.prepare_xls_parameters_list(working_sheets_data,
                                                    _get_parameters_configurable_list(learning_units,
                                                                                      titles_part1,
                                                                                      user))
    ws_data.update({xls_build.WORKSHEETS_DATA: [ws_data.get(xls_build.WORKSHEETS_DATA)[0], _prepare_legend_ws_data()]})
    return xls_build.generate_xls(ws_data, filters)


def _get_parameters_configurable_list(learning_units, titles, user):
    parameters = {
        xls_build.DESCRIPTION: XLS_DESCRIPTION,
        xls_build.USER: get_name_or_username(user),
        xls_build.FILENAME: XLS_FILENAME,
        xls_build.HEADER_TITLES: titles,
        xls_build.WS_TITLE: WORKSHEET_TITLE,
        xls_build.STYLED_CELLS: {
            WRAP_TEXT_STYLE: _get_wrapped_cells(
                learning_units,
                _get_col_letter(titles, HEADER_PROGRAMS),
                _get_col_letter(titles, HEADER_TEACHERS)
            )
        },
        xls_build.COLORED_ROWS: _get_colored_rows(learning_units),
    }
    return parameters


def _get_significant_volume(volume):
    if volume and volume > 0:
        return volume
    return ''


def _prepare_legend_ws_data():
    return {
        xls_build.HEADER_TITLES_KEY: [str(_('Legend'))],
        xls_build.CONTENT_KEY: [
            [SPACES, _('Proposal of creation')],
            [SPACES, _('Proposal for modification')],
            [SPACES, _('Suppression proposal')],
            [SPACES, _('Transformation proposal')],
            [SPACES, _('Transformation/modification proposal')],
        ],
        xls_build.WORKSHEET_TITLE_KEY: _('Legend'),
        xls_build.STYLED_CELLS:
            DEFAULT_LEGEND_STYLES
    }


def _get_wrapped_cells(learning_units, teachers_col_letter, programs_col_letter):
    dict_wrapped_styled_cells = []

    for idx, luy in enumerate(learning_units, start=2):
        if teachers_col_letter:
            dict_wrapped_styled_cells.append("{}{}".format(teachers_col_letter, idx))
        if programs_col_letter:
            dict_wrapped_styled_cells.append("{}{}".format(programs_col_letter, idx))

    return dict_wrapped_styled_cells


def _get_colored_rows(learning_units):
    colored_cells = defaultdict(list)
    for idx, luy in enumerate(learning_units, start=1):
        if getattr(luy, "proposallearningunit", None):
            colored_cells[PROPOSAL_LINE_STYLES.get(luy.proposallearningunit.type)].append(idx)
    return colored_cells


def _get_attribution_line(an_attribution):
    return "{} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} ".format(
        an_attribution.get('person'),
        _('Function'),
        Functions[an_attribution['function']].value if 'function' in an_attribution else '',
        _('Substitute'),
        an_attribution.get('substitute') if an_attribution.get('substitute') else '',
        _('Beg. of attribution'),
        an_attribution.get('start_year'),
        _('Attribution duration'),
        an_attribution.get('duration'),
        _('Attrib. vol1'),
        an_attribution.get('LECTURING'),
        _('Attrib. vol2'),
        an_attribution.get('PRACTICAL_EXERCISES'),
    )


def _get_col_letter(titles, title_search):
    for idx, title in enumerate(titles, start=1):
        if title == title_search:
            return get_column_letter(idx)
    return None


def _get_trainings_by_educ_group_year(learning_unit_yr):
    groups = []
    learning_unit_yr.group_elements_years = mdl_base.group_element_year.search(child_leaf=learning_unit_yr) \
        .select_related("child_leaf", "parent__education_group_type") \
        .order_by('parent__partial_acronym')
    groups.extend(learning_unit_yr.group_elements_years)
    education_groups_years = [group_element_year.parent for group_element_year in groups]
    return mdl_base.group_element_year \
        .find_learning_unit_formations(education_groups_years, parents_as_instances=True)


def _add_training_data(learning_unit_yr):
    formations_by_educ_group_year = _get_trainings_by_educ_group_year(learning_unit_yr)
    return "\n".join(["{}".format(_concatenate_training_data(formations_by_educ_group_year, group_element_year)) for
                      group_element_year in learning_unit_yr.group_elements_years])


def _concatenate_training_data(formations_by_educ_group_year, group_element_year):
    concatened_string = ''
    for training in formations_by_educ_group_year.get(group_element_year.parent_id):
        training_string = "{} {} {}".format(
            group_element_year.parent.partial_acronym if group_element_year.parent.partial_acronym else '',
            "({}) {}".format(
                '{0:.2f}'.format(
                    group_element_year.child_leaf.credits) if group_element_year.child_leaf.credits else '-',
                '-' if len(formations_by_educ_group_year.get(group_element_year.parent_id)) > 0 else ''),

            "{} - {}".format(training.acronym, training.title)
        )
        concatened_string = "{} {}\n".format(concatened_string, training_string)
    return concatened_string


def _get_data_part2(learning_unit_yr, with_attributions):
    lu_data_part2 = []
    if with_attributions:
        lu_data_part2.append(
            " \n".join(
                [_get_attribution_line(value)
                 for value in attribution_charge_new.find_attribution_charge_new_by_learning_unit_year_as_dict(
                    learning_unit_yr
                ).values()
                 ]
            )
        )

    lu_data_part2.extend([
        learning_unit_yr.get_periodicity_display(),
        yesno(learning_unit_yr.status),
        _get_significant_volume(learning_unit_yr.pm_vol_tot or 0),
        _get_significant_volume(learning_unit_yr.pm_vol_q1 or 0),
        _get_significant_volume(learning_unit_yr.pm_vol_q2 or 0),
        learning_unit_yr.pm_classes or 0,
        _get_significant_volume(learning_unit_yr.pp_vol_tot or 0),
        _get_significant_volume(learning_unit_yr.pp_vol_q1 or 0),
        _get_significant_volume(learning_unit_yr.pp_vol_q2 or 0),
        learning_unit_yr.pp_classes or 0,
        learning_unit_yr.get_quadrimester_display() or '',
        learning_unit_yr.get_session_display() or '',
        learning_unit_yr.language or "",
    ])
    return lu_data_part2


def _get_data_part1(learning_unit_yr):
    proposal = getattr(learning_unit_yr, "proposallearningunit", None)
    requirement_acronym = learning_unit_yr.entity_requirement
    allocation_acronym = learning_unit_yr.entity_allocation
    lu_data_part1 = [
        learning_unit_yr.acronym,
        learning_unit_yr.academic_year.name,
        learning_unit_yr.complete_title,
        learning_unit_yr.get_container_type_display(),
        learning_unit_yr.get_subtype_display(),
        requirement_acronym,
        proposal.get_type_display() if proposal else '',
        proposal.get_state_display() if proposal else '',
        learning_unit_yr.credits,
        allocation_acronym,
        learning_unit_yr.complete_title_english,
    ]
    return lu_data_part1
