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
import html
import itertools
import re
from collections import namedtuple, defaultdict

from django.conf import settings
from django.db.models import QuerySet, Prefetch, Exists, Subquery, OuterRef, Case, When
from django.template.defaultfilters import yesno
from django.utils.translation import gettext as _
from openpyxl import Workbook
from openpyxl.styles import Style, Border, Side, Color, PatternFill, Font
from openpyxl.styles.borders import BORDER_THICK
from openpyxl.styles.colors import RED, GREEN
from openpyxl.writer.excel import save_virtual_workbook

from attribution.business import attribution_charge_new
from backoffice.settings.base import LEARNING_UNIT_PORTAL_URL
from base.business.learning_unit import CMS_LABEL_PEDAGOGY, CMS_LABEL_PEDAGOGY_FR_AND_EN, CMS_LABEL_SPECIFICATIONS
from base.business.learning_unit_xls import volume_information, annotate_qs, PROPOSAL_LINE_STYLES, \
    prepare_proposal_legend_ws_data
from base.business.learning_units.xls_generator import hyperlinks_to_string, strip_tags
from base.models.education_group_year import EducationGroupYear
from base.models.enums.prerequisite_operator import OR, AND
from base.models.enums.proposal_type import ProposalType
from base.models.group_element_year import fetch_row_sql, GroupElementYear, get_all_group_elements_in_tree
from base.models.learning_achievement import LearningAchievement
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from base.models.prerequisite_item import PrerequisiteItem
from base.models.proposal_learning_unit import find_by_learning_unit_year
from base.models.teaching_material import TeachingMaterial
from cms.models.translated_text import TranslatedText
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from osis_common.document.xls_build import _build_worksheet, CONTENT_KEY, HEADER_TITLES_KEY, WORKSHEET_TITLE_KEY, \
    STYLED_CELLS, STYLE_NO_GRAY, COLORED_ROWS, ROW_HEIGHT
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.business.utils import html2text
from program_management.forms.custom_xls import CustomXlsForm


ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

BOLD_FONT = Font(bold=True)

STYLE_BORDER_BOTTOM = Style(
    border=Border(
        bottom=Side(
            border_style=BORDER_THICK, color=Color('FF000000')
        )
    )
)
STYLE_GRAY = Style(fill=PatternFill(patternType='solid', fgColor=Color('D1D1D1')))
STYLE_LIGHT_GRAY = Style(fill=PatternFill(patternType='solid', fgColor=Color('E1E1E1')))
STYLE_LIGHTER_GRAY = Style(fill=PatternFill(patternType='solid', fgColor=Color('F1F1F1')))

STYLE_FONT_RED = Style(font=Font(color=RED))
STYLE_FONT_GREEN = Style(font=Font(color=GREEN))
FONT_HYPERLINK = Font(underline='single', color='0563C1')

HeaderLine = namedtuple('HeaderLine', ['egy_acronym', 'egy_title', 'code_header', 'title_header', 'credits_header',
                                       'block_header', 'mandatory_header'])
OfficialTextLine = namedtuple('OfficialTextLine', ['text'])
LearningUnitYearLine = namedtuple('LearningUnitYearLine', ['luy_acronym', 'luy_title'])
PrerequisiteItemLine = namedtuple(
    'PrerequisiteItemLine',
    ['text', 'operator', 'luy_acronym', 'luy_title', 'credits', 'block', 'mandatory']
)
PrerequisiteOfItemLine = namedtuple(
    'PrerequisitedItemLine',
    ['text', 'luy_acronym', 'luy_title', 'credits', 'block', 'mandatory']

)
HeaderLinePrerequisiteOf = namedtuple('HeaderLinePrerequisiteOf', ['egy_acronym', 'egy_title', 'title_header',
                                                                   'credits_header', 'block_header',
                                                                   'mandatory_header'])

FIX_TITLES = [_('Code'), _('Ac yr.'), _('Title'), _('Type'), _('Subtype'), _('Gathering'), _('Cred. rel./abs.'),
              _('Block'), _('Mandatory')]

FixLineUEContained = namedtuple('FixLineUEContained', ['acronym', 'year', 'title', 'type', 'subtype', 'gathering',
                                                       'credits', 'block', 'mandatory'
                                                       ])

optional_header_for_required_entity = [_('Req. Entity')]
optional_header_for_proposition = [_('Proposal type'), _('Proposal status')]
optional_header_for_credits = [_('Credits')]
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
     'bibliography', 'mobility']
)

SpecificationsCols = namedtuple(
    'SpecificationsLine', [
        'themes_discussed', 'themes_discussed_en',
        'prerequisite', 'prerequisite_en',
        'achievements_fr', 'achievements_en'
    ]
)

LEGEND_WB_STYLE = 'colored_cells'
LEGEND_WB_CONTENT = 'content'


class EducationGroupYearLearningUnitsPrerequisitesToExcel:
    def __init__(self, egy: EducationGroupYear):
        self.egy = egy

    def get_queryset(self):
        group_element_years_of_education_group_year = [element["id"] for element in fetch_row_sql([self.egy.id])]
        return Prerequisite.objects.filter(
            education_group_year=self.egy
        ).prefetch_related(
            Prefetch(
                "prerequisiteitem_set",
                queryset=PrerequisiteItem.objects.order_by(
                    'group_number',
                    'position'
                ).select_related(
                    "learning_unit"
                ).prefetch_related(
                    Prefetch(
                        "learning_unit__learningunityear_set",
                        queryset=LearningUnitYear.objects.filter(
                            academic_year=self.egy.academic_year
                        ).prefetch_related(
                            Prefetch(
                                "child_leaf",
                                queryset=GroupElementYear.objects.filter(
                                    child_leaf__isnull=False,
                                    id__in=group_element_years_of_education_group_year
                                ),
                                to_attr="links"
                            )
                        ),
                        to_attr="luys"
                    )
                ),
                to_attr="items"
            )
        ).select_related(
            "learning_unit_year"
        ).order_by(
            "learning_unit_year__acronym"
        )

    def _to_workbook(self):
        return generate_prerequisites_workbook(self.egy, self.get_queryset())

    def to_excel(self):
        return save_virtual_workbook(self._to_workbook())


def generate_prerequisites_workbook(egy: EducationGroupYear, prerequisites_qs: QuerySet):
    worksheet_title = _("prerequisites-%(year)s-%(acronym)s") % {"year": egy.academic_year.year, "acronym": egy.acronym}
    worksheet_title = _clean_worksheet_title(worksheet_title)
    workbook = Workbook(encoding='utf-8')

    excel_lines = _build_excel_lines(egy, prerequisites_qs)

    return _get_workbook(egy, excel_lines, workbook, worksheet_title, 7)


def _build_excel_lines(egy: EducationGroupYear, prerequisite_qs: QuerySet):
    content = _first_line_content(
        HeaderLine(egy_acronym=egy.acronym,
                   egy_title=egy.title,
                   code_header=_('Code'),
                   title_header=_('Title'),
                   credits_header=_('Cred. rel./abs.'),
                   block_header=_('Block'),
                   mandatory_header=_('Mandatory'))
    )

    for prerequisite in prerequisite_qs:
        luy = prerequisite.learning_unit_year
        content.append(
            LearningUnitYearLine(luy_acronym=luy.acronym, luy_title=luy.complete_title_i18n)
        )
        groups_generator = itertools.groupby(prerequisite.items, key=lambda item: item.group_number)
        for key, group_gen in groups_generator:

            group = list(group_gen)
            for item in group:
                prerequisite_line = _build_prerequisite_line(prerequisite, item, group)
                content.append(prerequisite_line)

    return content


def _first_line_content(header_line):
    content = list()
    content.append(
        header_line
    )
    content.append(
        OfficialTextLine(text=_("Official"))
    )
    return content


def _build_prerequisite_line(prerequisite: Prerequisite, prerequisite_item: PrerequisiteItem, group: list):
    luy_item = prerequisite_item.learning_unit.luys[0]

    text = (_("has as prerequisite") + " :") \
        if prerequisite_item.group_number == 1 and prerequisite_item.position == 1 else None
    operator = _get_operator(prerequisite, prerequisite_item)
    luy_acronym = _get_item_acronym(prerequisite_item, group)
    credits = _get_item_credits(prerequisite_item)
    block = _get_item_blocks(prerequisite_item)
    mandatory = luy_item.links[0].is_mandatory if luy_item.links else None
    return PrerequisiteItemLine(
        text=text,
        operator=operator,
        luy_acronym=luy_acronym,
        luy_title=prerequisite_item.learning_unit.luys[0].complete_title_i18n,
        credits=credits,
        block=block,
        mandatory=_("Yes") if mandatory else _("No")
    )


def _get_operator(prerequisite: Prerequisite, prerequisite_item: PrerequisiteItem):
    if prerequisite_item.group_number == 1 and prerequisite_item.position == 1:
        return None
    elif prerequisite_item.position == 1:
        return _(prerequisite.main_operator)
    return _(prerequisite.secondary_operator)


def _get_item_acronym(prerequisite_item: PrerequisiteItem, group: list):
    acronym_format = "{acronym}"
    if prerequisite_item.position == 1 and len(group) > 1:
        acronym_format = "({acronym}"
    elif prerequisite_item.position == len(group) and len(group) > 1:
        acronym_format = "{acronym})"
    return acronym_format.format(acronym=prerequisite_item.learning_unit.luys[0].acronym)


def _get_item_credits(prerequisite_item: PrerequisiteItem):
    luy_item = prerequisite_item.learning_unit.luys[0]
    return " ; ".join(
        set(["{} / {:f}".format(grp.relative_credits, luy_item.credits.to_integral_value()) for grp in luy_item.links])
    )


def _get_item_blocks(prerequisite_item: PrerequisiteItem):
    luy_item = prerequisite_item.learning_unit.luys[0]
    return " ; ".join(
        [str(grp.block) for grp in luy_item.links if grp.block]
    )


def _get_style_to_apply(excel_lines: list):
    style_to_apply_dict = defaultdict(list)
    last_luy_line_index = None
    for index, row in enumerate(excel_lines, 1):
        if isinstance(row, HeaderLine):
            style_to_apply_dict[STYLE_NO_GRAY].append("A{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("B{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("C{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("D{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("E{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("F{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("G{index}".format(index=index))

        elif isinstance(row, OfficialTextLine):
            style_to_apply_dict[STYLE_BORDER_BOTTOM].append("A{index}".format(index=index))

        elif isinstance(row, LearningUnitYearLine):
            style_to_apply_dict[STYLE_GRAY].append("A{index}".format(index=index))
            style_to_apply_dict[STYLE_LIGHT_GRAY].append("B{index}".format(index=index))
            last_luy_line_index = index

        elif isinstance(row, PrerequisiteItemLine):
            if row.operator == _(OR):
                style_to_apply_dict[STYLE_FONT_RED].append("B{index}".format(index=index))
            elif row.operator == _(AND):
                style_to_apply_dict[STYLE_FONT_GREEN].append("B{index}".format(index=index))

            if (last_luy_line_index - index) % 2 == 1:
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("C{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("D{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("E{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("F{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("G{index}".format(index=index))
        elif isinstance(row, PrerequisiteOfItemLine):
            if (last_luy_line_index - index) % 2 == 1:
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("C{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("D{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("E{index}".format(index=index))
                style_to_apply_dict[STYLE_LIGHTER_GRAY].append("F{index}".format(index=index))
        if isinstance(row, HeaderLinePrerequisiteOf):
            style_to_apply_dict[STYLE_NO_GRAY].append("A{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("B{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("C{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("D{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("E{index}".format(index=index))
            style_to_apply_dict[STYLE_NO_GRAY].append("F{index}".format(index=index))
    return style_to_apply_dict


def _merge_cells(excel_lines, workbook: Workbook, end_column):
    worksheet = workbook.worksheets[0]
    for index, row in enumerate(excel_lines, 1):
        if isinstance(row, LearningUnitYearLine):
            worksheet.merge_cells(start_row=index, end_row=index, start_column=2, end_column=end_column)


def _add_hyperlink(excel_lines, workbook: Workbook, year):
    worksheet = workbook.worksheets[0]
    for index, row in enumerate(excel_lines, 1):
        if isinstance(row, LearningUnitYearLine):
            cell = worksheet.cell(row=index, column=1)
            cell.hyperlink = LEARNING_UNIT_PORTAL_URL.format(year=year, acronym=row.luy_acronym)
            cell.font = FONT_HYPERLINK

        if isinstance(row, PrerequisiteItemLine) or isinstance(row, PrerequisiteOfItemLine):
            column_nb = 3 if isinstance(row, PrerequisiteItemLine) else 2
            cell = worksheet.cell(row=index, column=column_nb)
            cell.hyperlink = LEARNING_UNIT_PORTAL_URL.format(year=year, acronym=row.luy_acronym.strip("()"))
            cell.font = FONT_HYPERLINK


class EducationGroupYearLearningUnitsIsPrerequisiteOfToExcel:

    def __init__(self, egy: EducationGroupYear):
        self.egy = egy
        self.hierarchy = EducationGroupHierarchy(root=self.egy)
        self.learning_unit_years_parent = {}

        for grp in self.hierarchy.included_group_element_years:
            if not grp.child_leaf:
                continue

            self.learning_unit_years_parent.setdefault(grp.child_leaf.id, grp)

    def get_queryset(self):
        is_prerequisite = PrerequisiteItem.objects.filter(
            learning_unit__learningunityear__id=OuterRef("child_leaf__id"),
            prerequisite__education_group_year=self.egy.id,
        )

        return GroupElementYear.objects.all() \
            .annotate(is_prerequisite=Exists(is_prerequisite)) \
            .select_related('child_branch__academic_year',
                            'child_branch__education_group_type',
                            'child_branch__administration_entity',
                            'child_branch__management_entity',
                            'child_leaf__academic_year',
                            'child_leaf__learning_container_year',
                            'child_leaf__learning_container_year__requirement_entity',
                            'child_leaf__learning_container_year__allocation_entity',
                            'child_leaf__proposallearningunit',
                            'child_leaf__externallearningunityear',
                            'parent') \
            .prefetch_related('child_branch__administration_entity__entityversion_set',
                              'child_branch__management_entity__entityversion_set',
                              'child_leaf__learning_container_year__requirement_entity__entityversion_set',
                              'child_leaf__learning_container_year__allocation_entity__entityversion_set'
                              ) \
            .order_by("order", "parent__partial_acronym")

    def _to_workbook(self):
        return generate_ue_is_prerequisite_for_workbook(self.egy, self.get_queryset(), self.learning_unit_years_parent)

    def to_excel(self):
        return save_virtual_workbook(self._to_workbook())


def generate_ue_is_prerequisite_for_workbook(egy: EducationGroupYear, prerequisites_qs: QuerySet,
                                             learning_unit_years_parent):
    worksheet_title = _("is_prerequisite_of-%(year)s-%(acronym)s") % {"year": egy.academic_year.year,
                                                                      "acronym": egy.acronym}
    worksheet_title = _clean_worksheet_title(worksheet_title)
    workbook = Workbook()

    excel_lines = _build_excel_lines_prerequisited(
        egy,
        get_all_group_elements_in_tree(egy, prerequisites_qs) or {},
        learning_unit_years_parent
    )
    return _get_workbook(egy, excel_lines, workbook, worksheet_title, 6)


def _get_workbook(egy, excel_lines, workbook, worksheet_title, end_column):
    header, *content = [tuple(line) for line in excel_lines]
    style = _get_style_to_apply(excel_lines)
    worksheet_data = {
        WORKSHEET_TITLE_KEY: worksheet_title,
        HEADER_TITLES_KEY: header,
        CONTENT_KEY: content,
        STYLED_CELLS: style
    }
    _build_worksheet(worksheet_data, workbook, 0)
    _merge_cells(excel_lines, workbook, end_column)
    _add_hyperlink(excel_lines, workbook, str(egy.academic_year.year))
    return workbook


def _build_excel_lines_prerequisited(egy: EducationGroupYear, prerequisite_qs: QuerySet, learning_unit_years_parent):
    content = _first_line_content(HeaderLinePrerequisiteOf(egy_acronym=egy.acronym,
                                                           egy_title=egy.title,
                                                           title_header=_('Title'),
                                                           credits_header=_('Cred. rel./abs.'),
                                                           block_header=_('Block'),
                                                           mandatory_header=_('Mandatory'))
                                  )

    for gey in prerequisite_qs:
        if gey.is_prerequisite:
            luy = gey.child
            content.append(
                LearningUnitYearLine(luy_acronym=luy.acronym, luy_title=luy.complete_title_i18n)
            )

            results = PrerequisiteItem.objects.filter(learning_unit=luy.learning_unit)

            first = True

            for result in results:
                if result.prerequisite.learning_unit_year.academic_year == luy.academic_year \
                        and result.prerequisite.education_group_year == egy:
                    prerequisite_line = _build_is_prerequisite_for_line(
                        result.prerequisite.learning_unit_year,
                        first,
                        learning_unit_years_parent
                    )
                    first = False
                    content.append(prerequisite_line)
    return content


def _build_is_prerequisite_for_line(luy_item, first, learning_unit_years_parent):
    text = (_("is a prerequisite of") + " :") if first else None

    luy_acronym = luy_item.acronym
    gey = learning_unit_years_parent.get(luy_item.id)

    credits = _get_credits_prerequisite_of(luy_item, gey)
    block = _get_blocks_prerequisite_of(gey)
    return PrerequisiteOfItemLine(
        text=text,
        luy_acronym=luy_acronym,
        luy_title=luy_item.complete_title_i18n,
        credits=credits,
        block=block,
        mandatory=_("Yes") if gey.is_mandatory else _("No")
    )


def _get_credits_prerequisite_of(luy_item, gey):
    if gey:
        relative_credits = gey.relative_credits
    else:
        relative_credits = ''
    return "{} / {:f}".format(relative_credits, luy_item.credits.to_integral_value())


def _get_blocks_prerequisite_of(gey):
    if gey:
        block_in_array = [i for i in str(gey.block)]
        return " ; ".join(
            block_in_array
        )
    return ''


def _clean_worksheet_title(title):
    # Worksheet title is max 25 chars (31 chars with sheet number) + does not accept slash present in acronyms
    return title[:25].replace("/", "_")


class EducationGroupYearLearningUnitsContainedToExcel:

    def __init__(self, egy: EducationGroupYear, custom_xls_form: CustomXlsForm):
        self.egy = egy
        self.hierarchy = EducationGroupHierarchy(root=self.egy)
        self.learning_unit_years_parent = []

        for grp in self.hierarchy.included_group_element_years:
            if not grp.child_leaf:
                continue
            self.learning_unit_years_parent.append(grp)
        self.custom_xls_form = custom_xls_form
        self._get_ordered_queryset()
        description_fiche = False
        specifications = False

        if custom_xls_form.is_valid():
            description_fiche = True if 'description_fiche' in custom_xls_form.fields else False
            specifications = True if 'specifications' in custom_xls_form.fields else False

        if description_fiche or specifications:
            self.qs = _annotate_with_description_fiche_specifications(self.qs, description_fiche, specifications)

    def _get_ordered_queryset(self):
        ids = []
        for luy in self.learning_unit_years_parent:
            ids.append(luy.id)
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        self.qs = GroupElementYear.objects.filter(id__in=ids).order_by(preserved)

    def _to_workbook(self):
        return generate_ue_contained_for_workbook(self.custom_xls_form, self.qs)

    def to_excel(self, ):
        return save_virtual_workbook(self._to_workbook())


def generate_ue_contained_for_workbook(custom_xls_form: CustomXlsForm, qs: QuerySet):
    data = _build_excel_lines_ues(custom_xls_form, qs)
    need_proposal_legend = custom_xls_form.is_valid() and custom_xls_form.cleaned_data['proposition']

    return _get_workbook_for_custom_xls(data.get('content'),
                                        need_proposal_legend,
                                        data.get('colored_cells'),
                                        data.get('row_height'))


def _build_excel_lines_ues(custom_xls_form: CustomXlsForm, qs: QuerySet):
    content = _get_headers(custom_xls_form)

    optional_data_needed = _optional_data(custom_xls_form)
    colored_cells = defaultdict(list)
    idx = 1

    for gey in qs:
        luy = gey.child_leaf
        content.append(_get_optional_data(_fix_data(gey, luy), luy, optional_data_needed, gey))
        if getattr(luy, "proposallearningunit", None):
            colored_cells[PROPOSAL_LINE_STYLES.get(luy.proposallearningunit.type)].append(idx)
        idx += 1

    colored_cells[Style(font=BOLD_FONT)].append(0)
    return {
        'content': content,
        'colored_cells': colored_cells,
        'row_height':
            {'height': 30,
             'start': 2,
             'stop': (len(content)) + 1}
            if optional_data_needed['has_description_fiche'] or optional_data_needed['has_specifications'] else {}
    }


def _optional_data(custom_xls_form):
    optional_data = _initialize_optional_data_dict(custom_xls_form)

    if custom_xls_form.is_valid():
        for field in custom_xls_form.fields:
            optional_data['has_{}'.format(field)] = custom_xls_form.cleaned_data[field]
    return optional_data


def _initialize_optional_data_dict(custom_xls_form):
    optional_data = {}
    for field in custom_xls_form.fields:
        optional_data['has_{}'.format(field)] = False
    return optional_data


def _get_headers(custom_xls_form):
    content = list()
    content.append(FIX_TITLES + _add_optional_titles(custom_xls_form))
    return content


def _fix_data(gey: GroupElementYear, luy: LearningUnitYear):
    data = []
    data_fix = FixLineUEContained(acronym=luy.acronym,
                                  year=luy.academic_year,
                                  title=luy.complete_title_i18n,
                                  type=luy.get_container_type_display(),
                                  subtype=luy.get_subtype_display(),
                                  gathering="{} - {}".format(gey.parent.partial_acronym, gey.parent.title),
                                  credits="{} / {}".format(gey.relative_credits or '-',
                                                           luy.credits.to_integral_value() or '-'),
                                  block=gey.block or '',
                                  mandatory=str.strip(yesno(gey.is_mandatory)))
    for name in data_fix._fields:
        data.append(getattr(data_fix, name))
    return data


def _get_workbook_for_custom_xls(excel_lines, need_proposal_legend, colored_cells, row_height=dict()):
    workbook = Workbook()
    worksheet_title = _clean_worksheet_title(_("List UE"))
    header, *content = [tuple(line) for line in excel_lines]

    worksheet_data = {
        WORKSHEET_TITLE_KEY: worksheet_title,
        HEADER_TITLES_KEY: header,
        CONTENT_KEY: content,
        STYLED_CELLS: {},
        COLORED_ROWS: colored_cells,
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


def _add_optional_titles(custom_xls_form):
    data = []
    if custom_xls_form.is_valid():
        for field in custom_xls_form.fields:
            if custom_xls_form.cleaned_data[field]:
                data = data + globals().get("optional_header_for_{}".format(field), [])
    return data


def _get_attribution_line(a_person_teacher):
    if a_person_teacher:
        return " ".join([
            (a_person_teacher.last_name or "").upper(),
            a_person_teacher.first_name or "",
            a_person_teacher.middle_name or ""
        ]).strip()
    return ""


def _get_optional_data(data, luy, optional_data_needed, gey):
    if optional_data_needed['has_required_entity']:
        data.append(luy.learning_container_year.requirement_entity)
    if optional_data_needed['has_allocation_entity']:
        data.append(luy.learning_container_year.allocation_entity)
    if optional_data_needed['has_credits']:
        data.append(luy.credits.to_integral_value() or '-')
    if optional_data_needed['has_periodicity']:
        data.append(luy.get_periodicity_display())
    if optional_data_needed['has_active']:
        data.append(str.strip(yesno(luy.status)))
    if optional_data_needed['has_quadrimester']:
        data.append(luy.get_quadrimester_display() or '')
    if optional_data_needed['has_session_derogation']:
        data.append(luy.get_session_display() or '')
    if optional_data_needed['has_volume']:
        luys = annotate_qs(LearningUnitYear.objects.filter(id=luy.id))
        data.extend(volume_information(luys[0]))
    if optional_data_needed['has_teacher_list']:
        attribution_values = attribution_charge_new.find_attribution_charge_new_by_learning_unit_year_as_dict(
                    luy
                ).values()
        data.append(
            ";".join(
                [_get_attribution_line(value.get('person'))
                 for value in attribution_values
                 ]
            )
        )
        data.append(
            ";".join(
                [value.get('person').email
                 for value in attribution_values
                 ]
            )
        )
    if optional_data_needed['has_proposition']:
        proposal = find_by_learning_unit_year(luy)
        if proposal:
            data.append(proposal.get_type_display())
            data.append(proposal.get_state_display())
        else:
            data.append('')
            data.append('')
    if optional_data_needed['has_english_title']:
        data.append(luy.complete_title_english)
    if optional_data_needed['has_language']:
        data.append(luy.language)
    if optional_data_needed['has_specifications']:
        specifications_data = _build_specifications_cols(luy, gey)
        for k, v in zip(specifications_data._fields, specifications_data):
            data.append(v)
    if optional_data_needed['has_description_fiche']:
        description_fiche = _build_description_fiche_cols(luy, gey)
        for k, v in zip(description_fiche._fields, description_fiche):
            data.append(v)
    return data


def _annotate_with_description_fiche_specifications(group_elt_yrs_param, description_fiche=False, specifications=False):
    group_element_years = group_elt_yrs_param
    sq = TranslatedText.objects.filter(
        reference=OuterRef('child_leaf__pk'),
        entity=LEARNING_UNIT_YEAR)
    if description_fiche:
        annotations = build_annotations(sq, CMS_LABEL_PEDAGOGY, CMS_LABEL_PEDAGOGY_FR_AND_EN)
        group_element_years = group_element_years.annotate(**annotations)

    if specifications:
        annotations = build_annotations(sq, CMS_LABEL_SPECIFICATIONS, CMS_LABEL_SPECIFICATIONS)
        group_element_years = group_element_years.annotate(**annotations)

    return group_element_years


def _build_validate_html_list_to_string(value_param, method):

    if method is None or method not in (hyperlinks_to_string, html2text):
        return value_param.strip()

    if value_param:
        # string must never be longer than 32,767 characters
        # truncate if necessary
        value = value_param.strip()
        value = value[:32767]
        value = method(html.unescape(value)) if value else ""
        if next(ILLEGAL_CHARACTERS_RE.finditer(value), None):
            return "!!! {}".format(_('IMPOSSIBLE TO DISPLAY BECAUSE OF AN ILLEGAL CHARACTER IN STRING'))
        return value

    return ""


def _build_specifications_cols(luy, gey):
    achievements_fr = LearningAchievement.objects.filter(
        learning_unit_year_id=luy.id,
        language__code=settings.LANGUAGE_CODE_FR[:2].upper()).order_by('order')

    achievements_en = LearningAchievement.objects.filter(
        learning_unit_year_id=luy.id,
        language__code=settings.LANGUAGE_CODE_EN[:2].upper()).order_by('order')

    return SpecificationsCols(
        themes_discussed=_build_validate_html_list_to_string(gey.themes_discussed, html2text),
        themes_discussed_en=_build_validate_html_list_to_string(gey.themes_discussed_en, html2text),
        prerequisite=_build_validate_html_list_to_string(gey.prerequisite, html2text),
        prerequisite_en=_build_validate_html_list_to_string(gey.prerequisite_en, html2text),
        achievements_fr=_build_achievements(achievements_fr),
        achievements_en=_build_achievements(achievements_en),
    )


def _build_achievements(achievements):
    achievements_str = ""
    for achievement in achievements:
        if achievement.text and achievement.text.strip() != "":
            if achievement.code_name:
                achievements_str += "{} -".format(achievement.code_name)
            achievements_str += _build_validate_html_list_to_string(achievement.text, html2text).lstrip('\n')
            achievements_str += '\n'
    return achievements_str.rstrip('\n')


def _build_description_fiche_cols(luy, gey):
    teaching_materials = TeachingMaterial.objects.filter(learning_unit_year_id=luy.id).order_by('order')
    return DescriptionFicheCols(
        resume=_build_validate_html_list_to_string(gey.resume, html2text),
        resume_en=_build_validate_html_list_to_string(gey.resume_en, html2text),
        teaching_methods=_build_validate_html_list_to_string(gey.teaching_methods, html2text),
        teaching_methods_en=_build_validate_html_list_to_string(gey.teaching_methods_en, html2text),
        evaluation_methods=_build_validate_html_list_to_string(gey.evaluation_methods, html2text),
        evaluation_methods_en=_build_validate_html_list_to_string(gey.evaluation_methods_en, html2text),
        other_informations=_build_validate_html_list_to_string(gey.other_informations, html2text),
        other_informations_en=_build_validate_html_list_to_string(gey.other_informations_en, html2text),
        online_resources=_build_validate_html_list_to_string(gey.online_resources, hyperlinks_to_string),
        online_resources_en=_build_validate_html_list_to_string(gey.online_resources_en, hyperlinks_to_string),
        teaching_materials=_build_validate_html_list_to_string(
            ''.join("<p>{} - {}</p>".format(_('Mandatory') if a.mandatory else _('Non-mandatory'), a.title)
                    for a in teaching_materials),
            html2text
        ),
        bibliography=_build_validate_html_list_to_string(gey.bibliography, html2text),
        mobility=_build_validate_html_list_to_string(gey.mobility, html2text)
    )


def build_annotations(sq: QuerySet, fr_labels: list, en_labels: list):
    annotations = {label_fr: Subquery(
        sq.filter(text_label__label=label_fr, language=settings.LANGUAGE_CODE_FR).values('text')[:1])
        for label_fr in fr_labels}

    annotations.update({
        "{}_en".format(label_en): Subquery(
            sq.filter(text_label__label="{}_en".format(label_en), language=settings.LANGUAGE_CODE_EN).values(
                'text')[:1])
        for label_en in en_labels}
    )
    return annotations
