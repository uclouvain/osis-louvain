##############################################################################
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
##############################################################################
import re
from collections import namedtuple, defaultdict
from typing import Dict, List

from django.conf import settings
from django.template.defaultfilters import yesno
from django.utils import translation
from django.utils.translation import gettext as _
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.excel import save_virtual_workbook

from attribution.ddd.domain.teacher import Teacher
from backoffice.settings.base import LANGUAGE_CODE_EN
from base.business.learning_unit_xls import PROPOSAL_LINE_STYLES, \
    prepare_proposal_legend_ws_data
from base.business.learning_unit_xls import get_significant_volume
from base.models.enums.education_group_types import GroupType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.learning_unit_year_subtypes import LEARNING_UNIT_YEAR_SUBTYPES
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.utils.excel import get_html_to_text
from learning_unit.ddd.domain.achievement import Achievement
from learning_unit.ddd.domain.description_fiche import DescriptionFiche
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear as DddLearningUnitYear
from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
from learning_unit.ddd.domain.teaching_material import TeachingMaterial
from learning_unit.ddd.repository.load_learning_unit_year import load_multiple_by_identity
from osis_common.ddd.interface import BusinessException
from osis_common.document.xls_build import _build_worksheet, CONTENT_KEY, HEADER_TITLES_KEY, WORKSHEET_TITLE_KEY, \
    STYLED_CELLS, ROW_HEIGHT, FONT_ROWS
from program_management.business.excel import clean_worksheet_title
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.command import SearchAllVersionsFromRootNodesCommand
from program_management.ddd.domain.exception import ProgramTreeVersionNotFoundException
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.ddd.service.read import get_program_tree_version_from_node_service
from program_management.ddd.service.read.search_all_versions_from_root_nodes import search_all_versions_from_root_nodes
from program_management.forms.custom_xls import CustomXlsForm

ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

BOLD_FONT = Font(bold=True)

optional_header_for_required_entity = [_('Req. Entity')]
optional_header_for_proposition = [_('Proposal type'), _('Proposal status')]
optional_header_for_credits = [_('Relative credits'), _('Absolute credits')]
optional_header_for_allocation_entity = [_('Alloc. Ent.')]
optional_header_for_english_title = [_('Title in English')]
optional_header_for_teacher_list = [_('List of teachers'), "{} ({})".format(_('List of teachers'), _('emails'))]
optional_header_for_periodicity = [_('Periodicity')]
optional_header_for_active = [_('Active')]
optional_header_for_volume = [
    '{} - {}'.format(_('Lecturing vol.'), _('Annual')),
    '{} - {}'.format(_('Lecturing vol.'), _('1st quadri')),
    '{} - {}'.format(_('Lecturing vol.'), _('2nd quadri')),
    _('Lecturing planned classes'),
    '{} - {}'.format(_('Practical vol.'), _('Annual')),
    '{} - {}'.format(_('Practical vol.'), _('1st quadri')),
    '{} - {}'.format(_('Practical vol.'), _('2nd quadri')),
    _('Practical planned classes'),

]
optional_header_for_quadrimester = [_('Quadrimester')]
optional_header_for_session_derogation = [_('Session derogation')]
optional_header_for_language = [_('Language')]
optional_header_for_description_fiche = [
    _('Content'), "{} {}".format(_('Content'), _('in English')),
    _('Teaching methods'), "{} {}".format(_('Teaching methods'), _('in English')),
    _('Evaluation methods'), "{} {}".format(_('Evaluation methods'), _('in English')),
    _('Other informations'), "{} {}".format(_('Other informations'), _('in English')),
    _('Online resources'), "{} {}".format(_('Online resources'), _('in English')),
    _('Teaching material'),
    _('bibliography').title(),
    _('Mobility'),
    _('Last update description fiche by'),
    _('Last update description fiche on')
]

optional_header_for_force_majeure = [
    _('Teaching methods (force majeure)'), "{} {}".format(_('Teaching methods (force majeure)'), _('in English')),
    _('Evaluation methods (force majeure)'), "{} {}".format(_('Evaluation methods (force majeure)'), _('in English')),
    _('Other informations (force majeure)'), "{} {}".format(_('Other informations (force majeure)'), _('in English')),
    _('Last update description fiche (force majeure) by'),
    _('Last update description fiche (force majeure) on')
]
optional_header_for_specifications = [
    _('Themes discussed'), "{} {}".format(_('Themes discussed'), _('in English')),
    _('Pre-condition'), "{} {}".format(_('Pre-condition'), _('in English')),
    _('Learning achievements'), "{} {}".format(_('Learning achievements'), _('in English')),
]

DescriptionFicheCols = namedtuple(
    'DescriptionFicheCols',
    ['resume', 'resume_en', 'teaching_methods', 'teaching_methods_en', 'evaluation_methods', 'evaluation_methods_en',
     'other_informations', 'other_informations_en', 'online_resources', 'online_resources_en', 'teaching_materials',
     'bibliography', 'mobility', 'last_update_by', 'last_update_date']
)

ForceMajeureCols = namedtuple(
    'ForceMajeureCols',
    ['teaching_methods_force_majeure', 'teaching_methods_force_majeure_en', 'evaluation_methods_force_majeure',
     'evaluation_methods_force_majeure_en', 'other_informations_force_majeure', 'other_informations_force_majeure_en',
     'last_update_by_force_majeure', 'last_update_date_force_majeure']
)
SpecificationsCols = namedtuple(
    'SpecificationsLine', [
        'themes_discussed', 'themes_discussed_en',
        'prerequisite', 'prerequisite_en',
        'achievements_fr', 'achievements_en'
    ]
)
FIX_TITLES = [_('Code'), _('Ac yr.'), _('Title'), _('Type'), _('Subtype'), _('Direct gathering'), _('Main gathering'),
              _('Block'), _('Mandatory')]

FixLineUEContained = namedtuple('FixLineUEContained', ['acronym', 'year', 'title', 'type', 'subtype', 'gathering',
                                                       'main_gathering', 'block', 'mandatory'
                                                       ])

LEGEND_WB_STYLE = 'colored_cells'
LEGEND_WB_CONTENT = 'content'

MAIN_GATHERING_KEY = 'main_gathering'
DIRECT_GATHERING_KEY = 'direct_gathering'
EXCLUDE_UE_KEY = 'exclude_ue'


class EducationGroupYearLearningUnitsContainedToExcel:

    def __init__(self, custom_xls_form: CustomXlsForm, year: int, code: str):
        self.program_tree_version = self._get_program_tree_version(code, year)
        self._get_program_tree(year, code)
        self.custom_xls_form = custom_xls_form

    def _get_program_tree_version(self, code: str, year: int):
        get_cmd = command.GetProgramTreeVersionFromNodeCommand(
            code=code,
            year=year
        )
        try:
            return get_program_tree_version_from_node_service.get_program_tree_version_from_node(
                get_cmd)
        except (BusinessException, ProgramTreeVersionNotFoundException):
            return None

    def _get_program_tree(self, year: int, code: str):
        if self.program_tree_version:
            self.hierarchy = self.program_tree_version.get_tree()
        else:
            self.hierarchy = ProgramTreeRepository.get(ProgramTreeIdentity(code, year))

    def _to_workbook(self):
        return generate_ue_contained_for_workbook(self.custom_xls_form, self.hierarchy)

    def to_excel(self):
        return {
            'workbook': save_virtual_workbook(self._to_workbook()),
            'title':
                _get_xls_title(self.hierarchy, self.program_tree_version),
            'year': self.hierarchy.root_node.year
        }


def generate_ue_contained_for_workbook(custom_xls_form: CustomXlsForm, hierarchy: 'ProgramTree'):
    data = _build_excel_lines_ues(custom_xls_form, hierarchy)
    need_proposal_legend = custom_xls_form.is_valid() and custom_xls_form.cleaned_data['proposition']
    return _get_workbook_for_custom_xls(data.get('content'),
                                        need_proposal_legend,
                                        data.get('font_rows'),
                                        data.get('row_height'))


def _build_excel_lines_ues(custom_xls_form: CustomXlsForm, tree: 'ProgramTree'):
    content = _get_headers(custom_xls_form)
    optional_data_needed = _optional_data(custom_xls_form)
    font_rows = defaultdict(list)
    idx = 1
    learning_unit_nodes = tree.get_all_learning_unit_nodes()

    if learning_unit_nodes:
        learning_unit_years = load_multiple_by_identity(
            [
                LearningUnitYearIdentity(code=learn_unt_child.code, year=learn_unt_child.year)
                for learn_unt_child in learning_unit_nodes
            ]
        )
    else:
        learning_unit_years = []

    tree_versions = search_all_versions_from_root_nodes(
        [
            SearchAllVersionsFromRootNodesCommand(code=node.code, year=node.year)
            for node in tree.get_all_nodes() if not node.is_learning_unit()
        ]
    )

    for path, child_node in tree.root_node.descendents:
        if child_node.is_learning_unit():
            luy = next(child for child in learning_unit_years if child_node.equals(child))

            parents = tree.get_parents(path)
            parents_data = get_explore_parents(parents)
            link = parents[0].get_direct_child(child_node.entity_id)

            if not parents_data[EXCLUDE_UE_KEY]:
                content.append(_get_optional_data(
                    _fix_data(link, luy, parents_data, tree_versions),
                    luy,
                    optional_data_needed,
                    link
                ))
                if luy.proposal and luy.proposal.type:
                    font_rows[PROPOSAL_LINE_STYLES.get(luy.proposal.type)].append(idx)
                idx += 1

    font_rows[BOLD_FONT].append(0)
    return {
        'content': content,
        'font_rows': font_rows,
        'row_height':
            {'height': 30,
             'start': 2,
             'stop': (len(content)) + 1}
            if optional_data_needed['has_description_fiche'] or optional_data_needed['has_specifications'] else {}
    }


def _optional_data(custom_xls_form: CustomXlsForm):
    optional_data = _initialize_optional_data_dict(custom_xls_form)

    if custom_xls_form.is_valid():
        for field in custom_xls_form.fields:
            optional_data['has_{}'.format(field)] = custom_xls_form.cleaned_data[field]
    return optional_data


def _initialize_optional_data_dict(custom_xls_form: CustomXlsForm):
    optional_data = {}
    for field in custom_xls_form.fields:
        optional_data['has_{}'.format(field)] = False
    return optional_data


def _get_headers(custom_xls_form: CustomXlsForm):
    content = list()
    content.append(FIX_TITLES + _add_optional_titles(custom_xls_form))
    return content


def _fix_data(
        link: 'Link',
        luy: 'LearningUnitYear',
        gathering: Dict[str, 'Node'],
        tree_versions: List['ProgramTreeVersion']
):
    data = []

    title = luy.full_title_fr
    if translation.get_language() == LANGUAGE_CODE_EN:
        title = luy.full_title_en
    data_fix = FixLineUEContained(
        acronym=luy.acronym,
        year=u"%s-%s" % (luy.year, str(luy.year + 1)[-2:]),
        title=title,
        type=luy.type.value if luy.type else '',
        subtype=dict(LEARNING_UNIT_YEAR_SUBTYPES)[luy.subtype] if luy.subtype else '',
        gathering=_build_direct_gathering_label(gathering[DIRECT_GATHERING_KEY]),
        main_gathering=_build_main_gathering_label(gathering[MAIN_GATHERING_KEY], tree_versions),
        block=link.block or '',
        mandatory=str.strip(yesno(link.is_mandatory))
    )
    for name in data_fix._fields:
        data.append(getattr(data_fix, name))
    return data


def _get_workbook_for_custom_xls(excel_lines: List, need_proposal_legend: bool, font_rows: dict, row_height=dict()):
    workbook = Workbook()
    worksheet_title = clean_worksheet_title(_("List UE"))
    header, *content = [tuple(line) for line in excel_lines]

    worksheet_data = {
        WORKSHEET_TITLE_KEY: worksheet_title,
        HEADER_TITLES_KEY: header,
        CONTENT_KEY: content,
        STYLED_CELLS: {},
        FONT_ROWS: font_rows,
        ROW_HEIGHT: row_height,

    }
    _build_worksheet(worksheet_data, workbook, 0)
    if need_proposal_legend:
        _build_worksheet(prepare_proposal_legend_ws_data(), workbook, 1)
    return workbook


def _build_legend_sheet():
    content = []
    colored_cells = defaultdict(list)
    idx = 1
    for name in ProposalType.get_names():
        content.append([ProposalType.get_value(name)])
        colored_cells[PROPOSAL_LINE_STYLES.get(name)].append(idx)
        idx += 1
    return {LEGEND_WB_STYLE: colored_cells, LEGEND_WB_CONTENT: content}


def _add_optional_titles(custom_xls_form: CustomXlsForm):
    data = []
    if custom_xls_form.is_valid():
        for field in custom_xls_form.fields:
            if custom_xls_form.cleaned_data[field]:
                if field == 'force_majeure' and not custom_xls_form.cleaned_data['description_fiche']:
                    data = data + globals().get("optional_header_for_description_fiche")
                data = data + globals().get("optional_header_for_{}".format(field), [])
    return data


def _get_attribution_line(a_person_teacher: 'Teacher'):
    if a_person_teacher:
        return " ".join([
            (a_person_teacher.last_name or "").upper(),
            a_person_teacher.first_name or "",
            a_person_teacher.middle_name or ""
        ]).strip()
    return ""


def _get_optional_data(data: List, luy: DddLearningUnitYear, optional_data_needed: Dict[str, bool], link: 'Link'):
    if optional_data_needed['has_required_entity']:
        data.append(luy.entities.requirement_entity_acronym)
    if optional_data_needed['has_allocation_entity']:
        data.append(luy.entities.allocation_entity_acronym)
    if optional_data_needed['has_credits']:
        data.append(link.relative_credits or '-')
        data.append(luy.credits.to_integral_value() or '-')
    if optional_data_needed['has_periodicity']:
        data.append(PeriodicityEnum[luy.periodicity.name].value if luy.periodicity else '')
    if optional_data_needed['has_active']:
        data.append(str.strip(yesno(luy.status)))
    if optional_data_needed['has_quadrimester']:
        data.append(luy.quadrimester.value if luy.quadrimester else '')
    if optional_data_needed['has_session_derogation']:
        data.append(luy.session or '')
    if optional_data_needed['has_volume']:
        data.extend(volumes_information(luy.lecturing_volume, luy.practical_volume))
    if optional_data_needed['has_teacher_list']:
        teachers = _get_distinct_teachers(
            luy
        )
        data.append(
            ";".join(
                [_get_attribution_line(teacher)
                 for teacher in teachers
                 ]
            )
        )
        data.append(
            ";".join(
                [teacher.email
                 for teacher in teachers
                 ]
            )
        )
    if optional_data_needed['has_proposition']:
        if luy.proposal:
            data.append(ProposalType.get_value(luy.proposal.type) if luy.proposal.type else '')
            data.append(ProposalState.get_value(luy.proposal.state) if luy.proposal.state else '')
        else:
            data.append('')
            data.append('')
    if optional_data_needed['has_english_title']:
        data.append(luy.full_title_en)
    if optional_data_needed['has_language']:
        data.append(luy.main_language)
    if optional_data_needed['has_specifications']:
        specifications_data = _build_specifications_cols(luy)
        for k, v in zip(specifications_data._fields, specifications_data):
            data.append(v)
    if optional_data_needed['has_description_fiche'] or optional_data_needed['has_force_majeure']:
        description_fiche = _build_description_fiche_cols(luy.description_fiche, luy.teaching_materials)
        for k, v in zip(description_fiche._fields, description_fiche):
            data.append(v)
        if optional_data_needed['has_force_majeure']:
            force_majeure = _build_force_majeure_cols(luy)
            for k, v in zip(force_majeure._fields, force_majeure):
                data.append(v)
    return data


def _build_force_majeure_cols(luy: 'DddLearningUnitYear'):
    force_majeure = luy.force_majeure
    return ForceMajeureCols(
        teaching_methods_force_majeure=_build_validate_html_list_to_string(
            force_majeure.teaching_methods
        ),
        teaching_methods_force_majeure_en=_build_validate_html_list_to_string(
            force_majeure.teaching_methods_en
        ),
        evaluation_methods_force_majeure=_build_validate_html_list_to_string(
            force_majeure.evaluation_methods
        ),
        evaluation_methods_force_majeure_en=_build_validate_html_list_to_string(
            force_majeure.evaluation_methods_en
        ),
        other_informations_force_majeure=_build_validate_html_list_to_string(
            force_majeure.other_informations
        ),
        other_informations_force_majeure_en=_build_validate_html_list_to_string(
            force_majeure.other_informations_en
        ),
        last_update_by_force_majeure=_build_validate_html_list_to_string(force_majeure.author),
        last_update_date_force_majeure=force_majeure.last_update.strftime('%d/%m/%Y')
        if force_majeure.last_update else None,
    )


def _build_validate_html_list_to_string(value_param):
    return get_html_to_text(value_param)


def _build_specifications_cols(luy: 'DddLearningUnitYear'):
    specifications = luy.specifications
    dict_achievement = _build_achievements(luy.achievements)
    return SpecificationsCols(
        themes_discussed=_build_validate_html_list_to_string(specifications.themes_discussed),
        themes_discussed_en=_build_validate_html_list_to_string(specifications.themes_discussed_en),
        prerequisite=_build_validate_html_list_to_string(specifications.prerequisite),
        prerequisite_en=_build_validate_html_list_to_string(specifications.prerequisite_en),
        achievements_fr=dict_achievement.get('achievements_fr', ''),
        achievements_en=dict_achievement.get('achievements_en', ''),
    )


def _build_achievements(achievements: List['Achievement']) -> Dict[str, str]:
    achievements_fr = ""
    achievements_en = ""
    if achievements:
        for achievement in achievements:
            if achievement.text_fr and achievement.text_fr.strip() != "":
                if achievement.code_name:
                    achievements_fr += "{} -".format(achievement.code_name)
                achievements_fr += _build_validate_html_list_to_string(achievement.text_fr).lstrip('\n')
                achievements_fr += '\n'

            if achievement.text_en and achievement.text_en.strip() != "":
                if achievement.code_name:
                    achievements_en += "{} -".format(achievement.code_name)
                achievements_en += _build_validate_html_list_to_string(achievement.text_en).lstrip('\n')
                achievements_en += '\n'
    return {
        'achievements_fr': achievements_fr.rstrip('\n'),
        'achievements_en': achievements_en.rstrip('\n')
    }


def _build_description_fiche_cols(description_fiche: 'DescriptionFiche',
                                  teaching_materials: List['TeachingMaterial']) -> DescriptionFicheCols:
    return DescriptionFicheCols(
        resume=_build_validate_html_list_to_string(description_fiche.resume),
        resume_en=_build_validate_html_list_to_string(description_fiche.resume_en),
        teaching_methods=_build_validate_html_list_to_string(description_fiche.teaching_methods),
        teaching_methods_en=_build_validate_html_list_to_string(description_fiche.teaching_methods_en),
        evaluation_methods=_build_validate_html_list_to_string(description_fiche.evaluation_methods),
        evaluation_methods_en=_build_validate_html_list_to_string(description_fiche.evaluation_methods_en),
        other_informations=_build_validate_html_list_to_string(description_fiche.other_informations),
        other_informations_en=_build_validate_html_list_to_string(description_fiche.other_informations_en),
        online_resources=_build_validate_html_list_to_string(description_fiche.online_resources),
        online_resources_en=_build_validate_html_list_to_string(description_fiche.online_resources_en),
        teaching_materials=_build_validate_html_list_to_string(
            ''.join("<p>{} - {}</p>".format(_('Mandatory') if a.is_mandatory else _('Non-mandatory'), a.title)
                    for a in teaching_materials)
        ),
        bibliography=_build_validate_html_list_to_string(description_fiche.bibliography),
        mobility=_build_validate_html_list_to_string(description_fiche.mobility),
        last_update_by=_build_validate_html_list_to_string(description_fiche.author),
        last_update_date=description_fiche.last_update.strftime('%d/%m/%Y')
        if description_fiche.last_update else None
    )


def _build_subquery_text_label(qs, cms_text_label, lang):
    return qs.filter(text_label__label="{}".format(cms_text_label), language=lang).values(
        'text')[:1]


def _build_direct_gathering_label(direct_gathering_node: 'NodeGroupYear') -> str:
    return "{} - {}".format(direct_gathering_node.code,
                            direct_gathering_node.group_title_fr or '') if direct_gathering_node else ''


def _build_main_gathering_label(gathering_node: 'Node', tree_versions: List['ProgramTreeVersion']) -> str:
    if gathering_node:
        pgm_tree_version = _get_program_tree_version_from_tree_versions_list(
            gathering_node.year, gathering_node.code, tree_versions
        )
        language = translation.get_language()
        node_title = _get_gathering_node_title(gathering_node, language)
        node_version_title = _get_gathering_node_version_title(pgm_tree_version, language)
        return "{}{} - {}{}".format(
            gathering_node.title,
            pgm_tree_version.version_label if pgm_tree_version else '',
            node_title,
            node_version_title
        )
    return '-'


def _get_gathering_node_title(gathering_node: 'Node', language: str):
    lang_suffix = 'en' if language == settings.LANGUAGE_CODE_EN else 'fr'
    field_prefix = 'group' if gathering_node.is_group() else 'offer'

    if gathering_node.is_finality():
        attr_name = '{}_partial_title_{}'.format(field_prefix, lang_suffix)
    else:
        attr_name = '{}_title_{}'.format(field_prefix, lang_suffix)
    return getattr(gathering_node, attr_name)


def _get_gathering_node_version_title(pgm_tree_version: 'ProgramTreeVersion', language: str):
    if pgm_tree_version and not pgm_tree_version.is_official_standard:
        if language == settings.LANGUAGE_CODE_EN and pgm_tree_version.title_en:
            return "[{}]".format(pgm_tree_version.title_en)
        elif language == settings.LANGUAGE_CODE_FR and pgm_tree_version.title_fr:
            return "[{}]".format(pgm_tree_version.title_fr)
    return ""


def volumes_information(lecturing_volume, practical_volume):
    return [get_significant_volume(lecturing_volume.total_annual or 0),
            get_significant_volume(lecturing_volume.first_quadrimester or 0),
            get_significant_volume(lecturing_volume.second_quadrimester or 0),
            lecturing_volume.classes_count or 0,
            get_significant_volume(practical_volume.total_annual or 0),
            get_significant_volume(practical_volume.first_quadrimester or 0),
            get_significant_volume(practical_volume.second_quadrimester or 0),
            practical_volume.classes_count or 0]


# FIXME :: to refactor because of cognitive complexity
def get_explore_parents(parents_of_ue: List['Node']) -> Dict[str, 'Node']:
    main_parent = None
    direct_parent = None
    exclude_ue_from_list = False
    if parents_of_ue:
        option_list = False
        for parent in parents_of_ue:
            if not direct_parent:
                direct_parent = parent

            if option_list and parent.is_finality():
                exclude_ue_from_list = True
            else:
                if main_parent is None \
                        and (parent.is_training()
                             or parent.is_mini_training()
                             or parent.node_type in [GroupType.COMPLEMENTARY_MODULE]):
                    main_parent = parent
            if parent.node_type in [GroupType.OPTION_LIST_CHOICE]:
                option_list = True
            if option_list and parent.is_finality():
                exclude_ue_from_list = True
            if exclude_ue_from_list:
                break

    return {
        MAIN_GATHERING_KEY: main_parent,
        DIRECT_GATHERING_KEY: direct_parent,
        EXCLUDE_UE_KEY: exclude_ue_from_list
    }


def _get_distinct_teachers(luy):
    teachers = []
    for attribution in luy.attributions:
        if attribution.teacher not in teachers:
            teachers.append(attribution.teacher)
    return teachers


def _get_program_tree_version_from_tree_versions_list(year: int, code: str, tree_versions: List['ProgramTreeVersion']):
    program_tree_identity = ProgramTreeIdentity(code=code, year=year)
    return next(
        (tree_version for tree_version in tree_versions
         if tree_version.program_tree_identity == program_tree_identity),
        None
    )


def _get_xls_title(tree: 'ProgramTree', program_tree_version: 'ProgramTreeVersion') -> str:
    return "{}{}".format(
        tree.root_node.title,
        program_tree_version.version_label
    ) if program_tree_version else tree.root_node.title
