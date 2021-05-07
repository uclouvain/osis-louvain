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
import datetime
import html
from unittest import mock

from django.template.defaultfilters import yesno
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from openpyxl.styles import Font

from attribution.ddd.domain.attribution import Attribution
from attribution.tests.ddd.factories.teacher import TeacherFactory
from base.business.learning_unit_xls import CREATION_COLOR, MODIFICATION_COLOR, TRANSFORMATION_COLOR, \
    TRANSFORMATION_AND_MODIFICATION_COLOR, SUPPRESSION_COLOR
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType, TrainingType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.enums.learning_unit_year_subtypes import LEARNING_UNIT_YEAR_SUBTYPES
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from ddd.logic.score_encoding.dtos import ScoreResponsibleDTO
from learning_unit.tests.ddd.factories.achievement import AchievementFactory
from learning_unit.tests.ddd.factories.description_fiche import DescriptionFicheFactory
from learning_unit.tests.ddd.factories.entities import EntitiesFactory
from learning_unit.tests.ddd.factories.learning_unit_year import LearningUnitYearFactory as DddLearningUnitYearFactory
from learning_unit.tests.ddd.factories.proposal import ProposalFactory
from learning_unit.tests.ddd.factories.specifications import SpecificationsFactory
from program_management.business.excel_ue_in_of import DIRECT_GATHERING_KEY, MAIN_GATHERING_KEY, EXCLUDE_UE_KEY, \
    optional_header_for_force_majeure
from program_management.business.excel_ue_in_of import FIX_TITLES, \
    _get_headers, optional_header_for_proposition, optional_header_for_credits, optional_header_for_volume, \
    _get_attribution_line, optional_header_for_required_entity, optional_header_for_active, \
    optional_header_for_allocation_entity, optional_header_for_description_fiche, optional_header_for_english_title, \
    optional_header_for_language, optional_header_for_periodicity, optional_header_for_quadrimester, \
    optional_header_for_session_derogation, optional_header_for_specifications, optional_header_for_teacher_list, \
    _fix_data, _get_workbook_for_custom_xls, _build_legend_sheet, LEGEND_WB_CONTENT, LEGEND_WB_STYLE, _optional_data, \
    _build_excel_lines_ues, _get_optional_data, BOLD_FONT, _build_validate_html_list_to_string, \
    _build_direct_gathering_label, _build_main_gathering_label, \
    get_explore_parents, _get_xls_title
from program_management.business.utils import html2text
from program_management.ddd.business_types import *
from program_management.ddd.domain.program_tree_version import version_label
from program_management.forms.custom_xls import CustomXlsForm
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory, \
    ProgramTreeVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory

PARTIAL_ACRONYM = 'Partial'

TITLE = 'Title'

CMS_TXT_WITH_LIST = '<ol> ' \
                    '<li>La structure atomique de la mati&egrave;re</li> ' \
                    '<li>Les diff&eacute;rentes structures mol&eacute;culaires</li> ' \
                    '</ol>'
CMS_TXT_WITH_LIST_AFTER_FORMATTING = 'La structure atomique de la matière\n' \
                                     'Les différentes structures moléculaires'

CMS_TXT_WITH_LINK = '<a href="https://moodleucl.uclouvain.be">moodle</a>'

LAST_UPDATE_BY = 'User_first_name_and_name'
LAST_UPDATE_DATE = datetime.datetime.now()


class TestGenerateEducationGroupYearLearningUnitsContainedWorkbook(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.element_root = ElementGroupYearFactory()
        cls.root = cls.element_root.group_year

        cls.child_1 = ElementGroupYearFactory()
        cls.child_2 = ElementGroupYearFactory()
        cls.learning_unit_year_2_1 = LearningUnitYearFactory()
        cls.child_2_1 = ElementLearningUnitYearFactory(learning_unit_year=cls.learning_unit_year_2_1)

        cls.node_1 = GroupElementYearFactory(parent_element=cls.element_root, child_element=cls.child_1)
        cls.node_2 = GroupElementYearFactory(parent_element=cls.element_root, child_element=cls.child_2)
        cls.node_2_1 = GroupElementYearFactory(parent_element=cls.child_2, child_element=cls.child_2_1)

        cls.root_node = NodeGroupYearFactory(node_id=cls.element_root.pk)

    def test_header_lines_without_optional_titles(self):
        custom_xls_form = CustomXlsForm({}, year=self.root_node.year, code=self.root_node.code)
        expected_headers = FIX_TITLES

        self.assertListEqual(_get_headers(custom_xls_form)[0], expected_headers)

    def test_header_lines_with_optional_titles(self):
        custom_xls_form = CustomXlsForm(
            {
                'required_entity': 'on',
                'allocation_entity': 'on',
                'credits': 'on',
                'periodicity': 'on',
                'active': 'on',
                'quadrimester': 'on',
                'session_derogation': 'on',
                'volume': 'on',
                'teacher_list': 'on',
                'proposition': 'on',
                'english_title': 'on',
                'language': 'on',
                'specifications': 'on',
                'description_fiche': 'on',
                'force_majeure': 'on'
            },
            year=self.root_node.year,
            code=self.root_node.code
        )

        expected_headers = \
            FIX_TITLES + optional_header_for_required_entity + optional_header_for_allocation_entity + \
            optional_header_for_credits + optional_header_for_periodicity + optional_header_for_active + \
            optional_header_for_quadrimester + optional_header_for_session_derogation + optional_header_for_volume + \
            optional_header_for_teacher_list + optional_header_for_proposition + optional_header_for_english_title + \
            optional_header_for_language + optional_header_for_specifications + optional_header_for_description_fiche \
            + optional_header_for_force_majeure
        self.assertListEqual(_get_headers(custom_xls_form)[0], expected_headers)

    def test_get_descritpion_fiche_header_if_force_majeure_checked(self):
        custom_xls_form = CustomXlsForm(
            {'force_majeure': 'on'},
            year=self.root_node.year,
            code=self.root_node.code
        )

        expected_headers = \
            FIX_TITLES + optional_header_for_description_fiche + optional_header_for_force_majeure
        self.assertListEqual(_get_headers(custom_xls_form)[0], expected_headers)

    def test_get_attribution_line(self):
        person = TeacherFactory(last_name='Last', first_name='First', middle_name='Middle')
        self.assertEqual(_get_attribution_line(person), 'LAST First Middle')
        person = TeacherFactory(last_name=None, first_name='First', middle_name='Middle')
        self.assertEqual(_get_attribution_line(person), 'First Middle')
        self.assertEqual(_get_attribution_line(None), '')


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.parent_node = NodeGroupYearFactory(node_type=TrainingType.BACHELOR)
        cls.child_node = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        cls.lu = NodeLearningUnitYearFactory()

        cls.link_1 = LinkFactory(parent=cls.parent_node, child=cls.child_node, is_mandatory=True)
        cls.link_1_1 = LinkFactory(parent=cls.child_node, child=cls.lu, is_mandatory=True)

        cls.ue_entities = EntitiesFactory(requirement_entity_acronym='ILV', allocation_entity_acronym='DRT')

        cls.teacher_1 = TeacherFactory(last_name='Dupont', first_name="Marcel", email="dm@gmail.com")
        cls.attribution_1 = Attribution(teacher=cls.teacher_1)
        cls.teacher_2 = TeacherFactory(last_name='Marseillais', first_name="Pol", email="pm@gmail.com")

        cls.attribution_2 = Attribution(teacher=cls.teacher_2)
        cls.achievement_1 = AchievementFactory(code_name="A1", text_fr="Text fr", text_en="Text en", entity_id="1")
        cls.achievement_2 = AchievementFactory(code_name="A2", text_fr="Text fr", text_en=None, entity_id="1")
        cls.achievement_3 = AchievementFactory(code_name="A3", text_fr=None, text_en="    ", entity_id="2")
        cls.achievement_4 = AchievementFactory(code_name=None, text_fr=None, text_en="    ", entity_id="2")

        specifications = initialize_cms_specifications_data_description_fiche()
        cls.luy = DddLearningUnitYearFactory(
            acronym=cls.lu.code,
            year=cls.lu.year,
            type=None,
            subtype=FULL,
            common_title_fr='Common fr',
            specific_title_fr='Specific fr',
            common_title_en='Common en',
            specific_title_en='Specific en',
            entities=cls.ue_entities,
            credits=cls.lu.credits,
            status=True,
            attributions=[cls.attribution_1, cls.attribution_2],
            achievements=[cls.achievement_1, cls.achievement_2, cls.achievement_3, cls.achievement_4],
            specifications=specifications
        )
        tree = ProgramTreeFactory(root_node=cls.parent_node)
        cls.tree_version = StandardProgramTreeVersionFactory(tree=tree)

        AcademicYearFactory(year=cls.luy.year)

    def test_fix_data(self):
        expected = get_expected_data_new(self.child_node, self.luy, self.link_1_1, self.link_1.parent)
        res = _fix_data(self.link_1_1,
                        self.luy,
                        {
                            DIRECT_GATHERING_KEY: self.child_node,
                            MAIN_GATHERING_KEY: self.parent_node,
                            EXCLUDE_UE_KEY: False
                        },
                        [self.tree_version])
        self.assertEqual(res, expected)

    def test_no_main_parent_result(self):
        root_node = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        link = LinkFactory(parent=root_node)
        root_node = link.parent

        self.assertIsNone(get_explore_parents([root_node])[MAIN_GATHERING_KEY])

    def test_main_parent_not_direct(self):
        #  To find main gathering loop up through the hierarchy till you find
        #  complementary module/formation/mini-formation
        root_node = NodeGroupYearFactory(category=Categories.TRAINING)
        group_level_1 = NodeGroupYearFactory(category=Categories.TRAINING)
        LinkFactory(parent=root_node,
                    child=group_level_1)

        group_level_2 = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        LinkFactory(parent=group_level_1, child=group_level_2)

        ue_level_3 = NodeLearningUnitYearFactory()
        LinkFactory(parent=group_level_2, child=ue_level_3)

        self.assertEqual(get_explore_parents([group_level_2, group_level_1, root_node])[MAIN_GATHERING_KEY],
                         group_level_1)

    def test_main_parent_complementary(self):
        # - root_node (code =code 1)
        #   |- group_level_1 (COMPLEMENTARY_MODULE) (code =code 2)
        #      | - group_level_2 (MAJOR_LIST_CHOICE) (code =code 3)
        #          | - ue_level_3 (code =code 4)
        root_node = NodeGroupYearFactory(category=Categories.TRAINING, node_id=1, code="code 1")
        group_level_1 = NodeGroupYearFactory(node_type=GroupType.COMPLEMENTARY_MODULE, node_id=2, code="code 2")
        LinkFactory(parent=root_node, child=group_level_1)

        group_level_2 = NodeGroupYearFactory(node_type=GroupType.MAJOR_LIST_CHOICE,
                                             category=Categories.GROUP, node_id=3, code="code 3")
        LinkFactory(parent=group_level_1, child=group_level_2)

        ue_level_3 = NodeLearningUnitYearFactory(node_id=4, code="code 4")
        LinkFactory(parent=group_level_2, child=ue_level_3)

        parents_data = get_explore_parents([group_level_2, group_level_1, root_node])
        self.assertEqual(parents_data[MAIN_GATHERING_KEY].node_id, group_level_1.node_id)

    def test_legend_workbook_exists(self):
        wb = _get_workbook_for_custom_xls([['header'], [['row1 col1']]], True, {})
        self.assertEqual(len(wb.worksheets), 2)

    def test_legend_workbook_do_not_exists(self):
        wb = _get_workbook_for_custom_xls([['header'], [['row1 col1']]], False, {})
        self.assertEqual(len(wb.worksheets), 1)

    def test_legend_workbook_content(self):
        expected_content = [[_("Creation")], [_("Modification")], [_("Transformation")],
                            [_("Transformation and modification")], [_("Suppression")]]

        data = _build_legend_sheet()
        self.assertListEqual(data.get(LEGEND_WB_CONTENT), expected_content)

    def test_legend_workbook_style(self):
        data = _build_legend_sheet()
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Font(color=CREATION_COLOR)), [1])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Font(color=MODIFICATION_COLOR)), [2])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Font(color=TRANSFORMATION_COLOR)), [3])
        self.assertListEqual(
            data.get(LEGEND_WB_STYLE).get(Font(color=TRANSFORMATION_AND_MODIFICATION_COLOR)),
            [4])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Font(color=SUPPRESSION_COLOR)), [5])

    def test_no_optional_data_to_add(self):
        form = CustomXlsForm({}, year=self.parent_node.year, code=self.parent_node.code)
        self.assertDictEqual(_optional_data(form),
                             {'has_required_entity': False,
                              'has_proposition': False,
                              'has_credits': False,
                              'has_allocation_entity': False,
                              'has_english_title': False,
                              'has_force_majeure': False,
                              'has_teacher_list': False,
                              'has_periodicity': False,
                              'has_active': False,
                              'has_volume': False,
                              'has_quadrimester': False,
                              'has_session_derogation': False,
                              'has_language': False,
                              'has_description_fiche': False,
                              'has_specifications': False,
                              'has_force_majeure': False
                              }
                             )

    def test_all_optional_data_to_add(self):
        form = CustomXlsForm({'required_entity': 'on',
                              'proposition': 'on',
                              'credits': 'on',
                              'allocation_entity': 'on',
                              'english_title': 'on',
                              'teacher_list': 'on',
                              'periodicity': 'on',
                              'active': 'on',
                              'volume': 'on',
                              'quadrimester': 'on',
                              'session_derogation': 'on',
                              'language': 'on',
                              'description_fiche': 'on',
                              'specifications': 'on',
                              'force_majeure': 'on'
                              },
                             year=self.parent_node.year,
                             code=self.parent_node.code
                             )
        self.assertDictEqual(_optional_data(form),
                             {'has_required_entity': True,
                              'has_proposition': True,
                              'has_credits': True,
                              'has_allocation_entity': True,
                              'has_english_title': True,
                              'has_force_majeure': True,
                              'has_teacher_list': True,
                              'has_periodicity': True,
                              'has_active': True,
                              'has_volume': True,
                              'has_quadrimester': True,
                              'has_session_derogation': True,
                              'has_language': True,
                              'has_description_fiche': True,
                              'has_specifications': True,
                              'has_force_majeure': True
                              }
                             )

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_get_optional_required_entity(self, mock_entity_is_active):
        optional_data = initialize_optional_data()
        optional_data['has_required_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.entities.requirement_entity_acronym])

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_get_optional_allocation_entity(self, mock_entity_is_active):
        optional_data = initialize_optional_data()
        optional_data['has_allocation_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.entities.allocation_entity_acronym])

    def test_get_optional_credits(self):
        optional_data = initialize_optional_data()
        optional_data['has_credits'] = True

        self.assertCountEqual(
            _get_optional_data([], self.luy, optional_data, self.link_1_1, []),
            [self.link_1_1.relative_credits or '-', self.luy.credits.to_integral_value() or '-']
        )

    def test_get_optional_has_periodicity(self):
        optional_data = initialize_optional_data()
        optional_data['has_periodicity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [PeriodicityEnum[self.luy.periodicity.name].value if self.luy.periodicity else ''])

    def test_get_optional_has_active(self):
        optional_data = initialize_optional_data()
        optional_data['has_active'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [_('yes')])

    def test_get_optional_has_quadrimester(self):
        optional_data = initialize_optional_data()
        optional_data['has_quadrimester'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.quadrimester or ''])

    def test_get_optional_has_session_derogation(self):
        optional_data = initialize_optional_data()
        optional_data['has_session_derogation'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.session or ''])

    def test_get_optional_has_proposition(self):
        optional_data = initialize_optional_data()
        optional_data['has_proposition'] = True
        luy_without_proposition = DddLearningUnitYearFactory(proposal=None)
        self.assertCountEqual(_get_optional_data([], luy_without_proposition, optional_data, self.link_1_1, []),
                              ['', ''])
        proposal = ProposalFactory()
        self.luy.proposal = proposal
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [ProposalType.get_value(self.luy.proposal.type),
                               ProposalState.get_value(self.luy.proposal.state)])

    def test_get_optional_has_english_title(self):
        optional_data = initialize_optional_data()
        optional_data['has_english_title'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.full_title_en])

    def test_get_optional_has_language(self):
        optional_data = initialize_optional_data()
        optional_data['has_language'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1, []),
                              [self.luy.main_language])

    def test_get_optional_has_teacher_list(self):
        optional_data = initialize_optional_data()
        optional_data['has_teacher_list'] = True
        teacher_data = _get_optional_data([], self.luy, optional_data, self.link_1_1, [])

        self._assert_teachers_data(teacher_data)
        self.assertEqual(teacher_data[2], "")
        self.assertEqual(teacher_data[3], "")

    def _assert_teachers_data(self, teacher_data):
        self.assertEqual(len(teacher_data), 4)
        self.assertEqual(teacher_data[0], "{} {};{} {}"
                         .format(self.teacher_1.last_name.upper(), self.teacher_1.first_name,
                                 self.teacher_2.last_name.upper(), self.teacher_2.first_name))
        self.assertEqual(teacher_data[1], "{};{}"
                         .format(self.teacher_1.email,
                                 self.teacher_2.email))

    def test_get_optional_has_teacher_with_score_responsible(self):
        optional_data = initialize_optional_data()
        optional_data['has_teacher_list'] = True
        responsible_1 = ScoreResponsibleDTO(
            last_name="Abba",
            first_name="Léon",
            email="abba@gmail.com",
            code_of_learning_unit=self.luy.acronym,
            year_of_learning_unit=self.luy.year
        )
        responsible_2 = ScoreResponsibleDTO(
            last_name="Martinot",
            first_name="Tom",
            email="martinot.tom@gmail.com",
            code_of_learning_unit=self.luy.acronym,
            year_of_learning_unit=self.luy.year
        )
        teacher_data = _get_optional_data(
            [],
            self.luy,
            optional_data,
            self.link_1_1,
            [
                responsible_1,
                responsible_2
            ]
        )
        self._assert_teachers_data(teacher_data)
        self.assertEqual(teacher_data[2], "{} {};{} {}"
                         .format(responsible_1.last_name.upper(), responsible_1.first_name,
                                 responsible_2.last_name.upper(), responsible_2.first_name)
                         )
        self.assertEqual(teacher_data[3], "{};{}"
                         .format(responsible_1.email,
                                 responsible_2.email)
                         )

    def test_build_validate_html_list_to_string(self):
        self.assertEqual(_build_validate_html_list_to_string(None), "")

    def test_build_validate_html_list_to_string_wrong_method(self):
        self.assertEqual(_build_validate_html_list_to_string('Test'), 'Test')

    def test_html_list_to_string(self):
        ch = '''<head></head>
                <body>
                <style type="text/css"></style>
                <ul>
                    <li>Cfr. Student corner</li>
                </ul>            
                <p>Cfr. Syllabus</p>
                <script>alert('coucou');</script>    
                </body>        
                '''
        expected = "Cfr. Student corner\nCfr. Syllabus"
        self.assertEqual(html2text(html.unescape(ch)), expected)

    def test_convert(self):
        res = html2text(html.unescape("<p>Introduire aux m&eacute;thodes d&#39;analyse</p>"))
        self.assertEqual(res, "Introduire aux méthodes d'analyse")

    def test_build_direct_gathering_label(self):
        node = NodeGroupYearFactory()
        self.assertEqual(_build_direct_gathering_label(None), '')
        self.assertEqual(_build_direct_gathering_label(node),
                         "{} - {}".format(node.code,
                                          node.group_title_fr or ''))

    def test_build_main_gathering_label_finality_master(self):
        edg_finality = NodeGroupYearFactory(node_type=TrainingType.MASTER_MS_120,
                                            offer_partial_title_fr='partial_title')
        tree_version = StandardProgramTreeVersionFactory(tree=ProgramTreeFactory(root_node=edg_finality))
        self.assertEqual(_build_main_gathering_label(edg_finality, [tree_version]),
                         "{} - {}".format(edg_finality.title, edg_finality.offer_partial_title_fr))

    def test_build_main_gathering_label_not_master(self):
        node_not_finality = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        tree_version = StandardProgramTreeVersionFactory(tree=ProgramTreeFactory(root_node=node_not_finality))
        self.assertEqual(_build_main_gathering_label(node_not_finality, [tree_version]),
                         "{} - {}".format(node_not_finality.title, node_not_finality.group_title_fr))


def initialize_optional_data():
    return {
        'has_required_entity': False,
        'has_allocation_entity': False,
        'has_credits': False,
        'has_periodicity': False,
        'has_active': False,
        'has_quadrimester': False,
        'has_force_majeure': False,
        'has_session_derogation': False,
        'has_volume': False,
        'has_teacher_list': False,
        'has_proposition': False,
        'has_english_title': False,
        'has_language': False,
        'has_description_fiche': False,
        'has_specifications': False,
        'has_force_majeure': False
    }


def _initialize_cms_data_description_fiche():
    return DescriptionFicheFactory(
        resume=CMS_TXT_WITH_LIST,
        resume_en=CMS_TXT_WITH_LIST,
        teaching_methods=CMS_TXT_WITH_LIST,
        teaching_methods_en=CMS_TXT_WITH_LIST,
        evaluation_methods=CMS_TXT_WITH_LIST,
        evaluation_methods_en=CMS_TXT_WITH_LIST,
        other_informations=CMS_TXT_WITH_LIST,
        other_informations_en=CMS_TXT_WITH_LIST,
        bibliography=CMS_TXT_WITH_LIST,
        mobility=CMS_TXT_WITH_LIST,
        online_resources=CMS_TXT_WITH_LINK,
        online_resources_en=CMS_TXT_WITH_LINK,
    )


def initialize_cms_specifications_data_description_fiche():
    return SpecificationsFactory(
        prerequisite=CMS_TXT_WITH_LIST,
        prerequisite_en=CMS_TXT_WITH_LIST,
        themes_discussed=CMS_TXT_WITH_LIST,
        themes_discussed_en=CMS_TXT_WITH_LIST
    )


def get_expected_data_new(child_node, luy, link, main_gathering=None):
    gathering_str = "{} - {}".format(child_node.code, child_node.group_title_fr or '') if child_node else ''
    if main_gathering:
        main_gathering_str = "{} - {}".format(
            main_gathering.title,
            main_gathering.offer_partial_title_fr or '' if main_gathering.is_finality()
            else main_gathering.offer_title_fr
        ) if main_gathering else ''
    else:
        main_gathering_str = ''

    expected = [luy.acronym,
                u"%s-%s" % (luy.year, str(luy.year + 1)[-2:]),
                luy.full_title_fr,
                luy.type.value if luy.type else '',
                dict(LEARNING_UNIT_YEAR_SUBTYPES)[luy.subtype] if luy.subtype else '',
                gathering_str,
                main_gathering_str,
                link.block or '',
                _('yes')
                ]
    return expected


class TestXlsContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        # - root_node (PGRM_MASTER_120) (code =C1)
        #   |- group_level_1 (code =C2)
        #      | - group_level_1_1 (code =C3)
        #          | - ue1 (UE1)
        #          | - ue2 (UE2)
        #   | - group_level_2 (MASTER_MS_120) (code =C4)
        #       | - group_level_2_1 (COMMON_CORE) (code =C5)
        #           | - ue3 (UE3)
        #       | - group_level_2_2 (OPTION_LIST_CHOICE)(code =C6)
        #           | - ue4 (UE4)

        cls.root_node = NodeGroupYearFactory(node_id=1, code='C1', node_type=TrainingType.PGRM_MASTER_120)
        cls.academic_year = AcademicYearFactory(year=cls.root_node.year)
        cls.group_level_1 = NodeGroupYearFactory(node_id=2, code='C2', year=cls.academic_year.year)
        LinkFactory(parent=cls.root_node,
                    child=cls.group_level_1)

        cls.group_level_1_1 = NodeGroupYearFactory(node_id=3, code='C3', year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_1,
                    child=cls.group_level_1_1)

        cls.ue1 = NodeLearningUnitYearFactory(node_id=4, code='UE1', year=cls.academic_year.year)
        cls.link_group_level_1_1_and_ue1 = LinkFactory(parent=cls.group_level_1_1, child=cls.ue1)
        ue_2 = NodeLearningUnitYearFactory(node_id=5, code='UE2', year=cls.academic_year.year)
        cls.link_group_level_1_1_and_ue2 = LinkFactory(parent=cls.group_level_1_1, child=ue_2)

        cls.group_level_2 = NodeGroupYearFactory(node_id=6,
                                                 node_type=TrainingType.MASTER_MS_120,
                                                 year=cls.academic_year.year,
                                                 code='C4')
        LinkFactory(parent=cls.root_node,
                    child=cls.group_level_2)

        cls.group_level_2_1 = NodeGroupYearFactory(node_id=7,
                                                   node_type=GroupType.COMMON_CORE,
                                                   year=cls.academic_year.year,
                                                   code='C5')
        LinkFactory(parent=cls.group_level_2,
                    child=cls.group_level_2_1)
        cls.ue3 = NodeLearningUnitYearFactory(node_id=9, code='UE3', year=cls.academic_year.year)
        cls.link_group_level_2_1_and_ue3 = LinkFactory(parent=cls.group_level_2_1, child=cls.ue3)
        cls.group_level_2_2 = NodeGroupYearFactory(node_id=8,
                                                   node_type=GroupType.OPTION_LIST_CHOICE,
                                                   year=cls.academic_year.year,
                                                   code='C6')
        LinkFactory(parent=cls.group_level_2,
                    child=cls.group_level_2_2)
        cls.ue4 = NodeLearningUnitYearFactory(node_id=10, year=cls.academic_year.year, code='UE4')
        LinkFactory(parent=cls.group_level_2_2,
                    child=cls.ue4)

        cls.tree = ProgramTreeFactory(root_node=cls.root_node)

        # TODO : remplacer ce qui suit pour un accès plus direct

        cls.element_ue_1 = ElementLearningUnitYearFactory(id=cls.ue1.node_id,
                                                          learning_unit_year=LearningUnitYearFactory(
                                                              acronym=cls.ue1.code, academic_year=cls.academic_year)
                                                          )
        cls.element_ue_2 = ElementLearningUnitYearFactory(id=ue_2.node_id,
                                                          learning_unit_year=LearningUnitYearFactory(
                                                              acronym=ue_2.code, academic_year=cls.academic_year)
                                                          )
        cls.element_ue_3 = ElementLearningUnitYearFactory(id=cls.ue3.node_id,
                                                          learning_unit_year=LearningUnitYearFactory(
                                                              acronym=cls.ue3.code, academic_year=cls.academic_year)
                                                          )
        ElementLearningUnitYearFactory(id=cls.ue4.node_id,
                                       learning_unit_year=LearningUnitYearFactory(acronym=cls.ue4.code,
                                                                                  academic_year=cls.academic_year))

        cls.learning_units = [cls.element_ue_1.learning_unit_year, cls.element_ue_2.learning_unit_year,
                              cls.element_ue_3.learning_unit_year]
        cls.luy_count = len(cls.learning_units)

    def test_row_height_not_populated(self):
        custom_form = CustomXlsForm({}, year=self.root_node.year, code=self.root_node.code)
        data = _build_excel_lines_ues(custom_form, self.tree)
        self.assertDictEqual(data.get('row_height'), {})

    def test_row_height_populated(self):
        custom_form = CustomXlsForm({'description_fiche': 'on'}, year=self.root_node.year, code=self.root_node.code)
        data = _build_excel_lines_ues(custom_form, self.tree)

        self.assertDictEqual(data.get('row_height'), {
            'height': 30,
            'start': 2,
            'stop': self.luy_count + 2
        })

    def test_header_line(self):
        custom_form = CustomXlsForm({}, year=self.root_node.year, code=self.root_node.code)
        data = _build_excel_lines_ues(custom_form, self.tree)
        # First line (Header line) is always bold
        self.assertListEqual(data.get('font_rows')[BOLD_FONT], [0])

    def test_exclude_options_list_for_2M(self):
        self._assert_correct_ue_present_in_xls2(self.tree, ['UE1', 'UE2', 'UE3'])

    def test_do_not_exclude_options_list_if_not_2M(self):
        bachelor_root_node = NodeGroupYearFactory(node_type=TrainingType.BACHELOR, year=self.academic_year.year)

        group_level_1 = NodeGroupYearFactory(year=self.academic_year.year)
        LinkFactory(parent=bachelor_root_node,
                    child=group_level_1)

        group_level_1_1 = NodeGroupYearFactory(year=self.academic_year.year)
        LinkFactory(parent=group_level_1,
                    child=group_level_1_1)

        ue_level_group_level_1_1 = NodeLearningUnitYearFactory(code='UE21', node_id=100, year=self.academic_year.year)
        LinkFactory(parent=group_level_1_1,
                    child=ue_level_group_level_1_1)
        second_ue_level_group_level_1_1 = NodeLearningUnitYearFactory(code='UE22',
                                                                      node_id=101,
                                                                      year=self.academic_year.year)
        LinkFactory(parent=group_level_1_1,
                    child=second_ue_level_group_level_1_1)

        group_level_2 = NodeGroupYearFactory(node_id=6,
                                             node_type=GroupType.OPTION_LIST_CHOICE,
                                             year=self.academic_year.year)
        LinkFactory(parent=bachelor_root_node,
                    child=group_level_2)

        ue_level_group_level_2 = NodeLearningUnitYearFactory(code='UE23', node_id=102, year=self.academic_year.year)
        LinkFactory(parent=group_level_2,
                    child=ue_level_group_level_2)
        bachelor_tree = ProgramTreeFactory(root_node=bachelor_root_node)
        # TODO : remplacer ce qui suit pour un accès plus direct
        ElementLearningUnitYearFactory(id=ue_level_group_level_1_1.node_id,
                                       learning_unit_year=LearningUnitYearFactory(acronym='UE21',
                                                                                  academic_year=self.academic_year))
        ElementLearningUnitYearFactory(id=second_ue_level_group_level_1_1.node_id,
                                       learning_unit_year=LearningUnitYearFactory(
                                           acronym='UE22',
                                           academic_year=self.academic_year
                                       )
                                       )
        ElementLearningUnitYearFactory(id=ue_level_group_level_2.node_id,
                                       learning_unit_year=LearningUnitYearFactory(acronym='UE23',
                                                                                  academic_year=self.academic_year)
                                       )

        self._assert_correct_ue_present_in_xls2(bachelor_tree, ['UE21', 'UE22', 'UE23'])

    def test_get_title_with_version_name(self):
        tree_version = ProgramTreeVersionFactory(version_name='CEMS')
        tree = tree_version.tree

        self.assertEqual(_get_xls_title(tree_version.tree, tree_version), _assert_format_title(tree, tree_version))

    def test_get_title_without_version_name(self):
        tree_version = StandardProgramTreeVersionFactory()
        tree = tree_version.tree

        self.assertEqual(_get_xls_title(tree_version.tree, tree_version), _assert_format_title(tree, tree_version))

    def test_link_data(self):
        custom_form = CustomXlsForm({'credits': 'on'}, year=self.tree.root_node.year, code=self.tree.root_node.code)
        data = _build_excel_lines_ues(custom_form, self.tree)
        content = data['content']

        self._assert_correct_data_from_link(content[1],
                                            self.link_group_level_1_1_and_ue1,
                                            self.element_ue_1.learning_unit_year)
        self._assert_correct_data_from_link(content[2],
                                            self.link_group_level_1_1_and_ue2,
                                            self.element_ue_2.learning_unit_year)
        self._assert_correct_data_from_link(content[3],
                                            self.link_group_level_2_1_and_ue3,
                                            self.element_ue_3.learning_unit_year)

    def _assert_correct_ue_present_in_xls2(self, tree, ues):
        data = _build_excel_lines_ues(CustomXlsForm({}, year=self.root_node.year, code=self.root_node.code), tree)
        content = data['content']
        del content[0]
        self.assertEqual(len(content), len(ues))
        self.assertCountEqual([content[0][0], content[1][0], content[2][0]],
                              ues)

    def _assert_correct_data_from_link(self, ue_content, link, learning_unit_year):
        self.assertEqual(ue_content[7], link.block or '')
        self.assertEqual(ue_content[8], str.strip(yesno(link.is_mandatory)))
        self.assertEqual(ue_content[9], link.relative_credits or '-')
        self.assertEqual(ue_content[10], learning_unit_year.credits or '')


def _assert_format_title(tree: 'ProgramTree', tree_version: 'ProgramTreeVersion') -> str:
    return "{}{}".format(
        tree.root_node.title,
        version_label(tree_version.entity_id)
    ) if tree_version else tree.root_node.title
