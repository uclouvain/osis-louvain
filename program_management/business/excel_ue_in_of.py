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
import re
from collections import namedtuple, defaultdict

from django.conf import settings
from django.db.models import QuerySet, Subquery, OuterRef, Case, When
from django.template.defaultfilters import yesno
from django.utils.translation import gettext as _
from openpyxl import Workbook
from openpyxl.styles import Style, Font
from openpyxl.writer.excel import save_virtual_workbook

from attribution.business import attribution_charge_new
from base.business.learning_unit import CMS_LABEL_PEDAGOGY, CMS_LABEL_PEDAGOGY_FR_AND_EN, CMS_LABEL_SPECIFICATIONS
from base.business.learning_unit_xls import volume_information, annotate_qs, PROPOSAL_LINE_STYLES, \
    prepare_proposal_legend_ws_data
from base.business.learning_units.xls_generator import hyperlinks_to_string
from base.models.education_group_year import EducationGroupYear
from base.models.enums.proposal_type import ProposalType
from base.models.group_element_year import GroupElementYear
from base.models.learning_achievement import LearningAchievement
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import find_by_learning_unit_year
from base.models.teaching_material import TeachingMaterial
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from osis_common.document.xls_build import _build_worksheet, CONTENT_KEY, HEADER_TITLES_KEY, WORKSHEET_TITLE_KEY, \
    STYLED_CELLS, COLORED_ROWS, ROW_HEIGHT
from program_management.business.excel import clean_worksheet_title
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.business.utils import html2text
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
FIX_TITLES = [_('Code'), _('Ac yr.'), _('Title'), _('Type'), _('Subtype'), _('Direct gathering'), _('Main gathering'),
              _('Block'), _('Mandatory')]

FixLineUEContained = namedtuple('FixLineUEContained', ['acronym', 'year', 'title', 'type', 'subtype', 'gathering',
                                                       'main_gathering', 'block', 'mandatory'
                                                       ])

LEGEND_WB_STYLE = 'colored_cells'
LEGEND_WB_CONTENT = 'content'


class EducationGroupYearLearningUnitsContainedToExcel:

    def __init__(self, root: EducationGroupYear, egy: EducationGroupYear, custom_xls_form: CustomXlsForm):
        self.egy = egy

        exclude_options = True if self.egy.is_master120 or self.egy.is_master180 else False
        self.root_hierarchy = EducationGroupHierarchy(root=root, exclude_options=exclude_options)
        hierarchy = EducationGroupHierarchy(root=self.egy, exclude_options=exclude_options)
        self.learning_unit_years_parent = []

        for grp in hierarchy.included_group_element_years:
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
        return generate_ue_contained_for_workbook(self.custom_xls_form, self.qs, self.root_hierarchy)

    def to_excel(self, ):
        return save_virtual_workbook(self._to_workbook())


def generate_ue_contained_for_workbook(custom_xls_form: CustomXlsForm, qs: QuerySet, hierarchy):
    data = _build_excel_lines_ues(custom_xls_form, qs, hierarchy)
    need_proposal_legend = custom_xls_form.is_valid() and custom_xls_form.cleaned_data['proposition']

    return _get_workbook_for_custom_xls(data.get('content'),
                                        need_proposal_legend,
                                        data.get('colored_cells'),
                                        data.get('row_height'))


def _build_excel_lines_ues(custom_xls_form: CustomXlsForm, qs: QuerySet, hierarchy):
    content = _get_headers(custom_xls_form)

    optional_data_needed = _optional_data(custom_xls_form)
    colored_cells = defaultdict(list)
    idx = 1

    for gey in qs:
        luy = gey.child_leaf
        content.append(_get_optional_data(_fix_data(gey, luy, hierarchy), luy, optional_data_needed, gey))
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


def _fix_data(gey: GroupElementYear, luy: LearningUnitYear, hierarchy):
    data = []

    main_gathering = hierarchy.get_main_parent(gey.parent.id)

    data_fix = FixLineUEContained(acronym=luy.acronym,
                                  year=luy.academic_year,
                                  title=luy.complete_title_i18n,
                                  type=luy.get_container_type_display(),
                                  subtype=luy.get_subtype_display(),
                                  gathering=_build_gathering_content(gey.parent),
                                  main_gathering=_build_main_gathering_content(main_gathering),
                                  block=gey.block or '',
                                  mandatory=str.strip(yesno(gey.is_mandatory)))
    for name in data_fix._fields:
        data.append(getattr(data_fix, name))
    return data


def _get_workbook_for_custom_xls(excel_lines, need_proposal_legend, colored_cells, row_height=dict()):
    workbook = Workbook()
    worksheet_title = clean_worksheet_title(_("List UE"))
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
        data.append(gey.relative_credits or '-')
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


def build_annotations(qs: QuerySet, fr_labels: list, en_labels: list):
    annotations = {
        lbl: Subquery(
            _build_subquery_text_label(qs, lbl, settings.LANGUAGE_CODE_FR))
        for lbl in fr_labels
    }

    annotations.update({
        "{}_en".format(lbl): Subquery(
            _build_subquery_text_label(qs, lbl, settings.LANGUAGE_CODE_EN))
        for lbl in en_labels}
    )
    return annotations


def _build_subquery_text_label(qs, cms_text_label, lang):
    return qs.filter(text_label__label="{}".format(cms_text_label), language=lang).values(
        'text')[:1]


def _build_gathering_content(edg):
    return "{} - {}".format(edg.partial_acronym, edg.title) if edg else ''


def _build_main_gathering_content(edg):
    return "{} - {}".format(edg.acronym, edg.partial_title if edg.is_finality else edg.title) if edg else ''
