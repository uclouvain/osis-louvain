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
import html

from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from openpyxl.styles import Font

from attribution.ddd.domain.attribution import Attribution
from attribution.tests.ddd.factories.teacher import TeacherFactory
from base.business.learning_unit_xls import CREATION_COLOR, MODIFICATION_COLOR, TRANSFORMATION_COLOR, \
    TRANSFORMATION_AND_MODIFICATION_COLOR, SUPPRESSION_COLOR
from base.models.enums import education_group_types
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType, TrainingType
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import GroupFactory, TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from learning_unit.tests.ddd.factories.achievement import AchievementFactory
from learning_unit.tests.ddd.factories.description_fiche import DescriptionFicheFactory
from learning_unit.tests.ddd.factories.entities import EntitiesFactory
from learning_unit.tests.ddd.factories.learning_unit_year import LearningUnitYearFactory as DddLearningUnitYearFactory
from learning_unit.tests.ddd.factories.proposal import ProposalFactory
from learning_unit.tests.ddd.factories.specifications import SpecificationsFactory
from learning_unit.tests.ddd.factories.teaching_material import TeachingMaterialFactory as DddTeachingMaterialFactory
from program_management.business.excel_ue_in_of import DIRECT_GATHERING_KEY, MAIN_GATHERING_KEY, EXCLUDE_UE_KEY
from program_management.business.excel_ue_in_of import FIX_TITLES, \
    _get_headers, optional_header_for_proposition, optional_header_for_credits, optional_header_for_volume, \
    _get_attribution_line, optional_header_for_required_entity, optional_header_for_active, \
    optional_header_for_allocation_entity, optional_header_for_description_fiche, optional_header_for_english_title, \
    optional_header_for_language, optional_header_for_periodicity, optional_header_for_quadrimester, \
    optional_header_for_session_derogation, optional_header_for_specifications, optional_header_for_teacher_list, \
    _fix_data, _get_workbook_for_custom_xls, _build_legend_sheet, LEGEND_WB_CONTENT, LEGEND_WB_STYLE, _optional_data, \
    _build_excel_lines_ues, _get_optional_data, BOLD_FONT, _build_specifications_cols, _build_description_fiche_cols, \
    _build_validate_html_list_to_string, _build_direct_gathering_label, _build_main_gathering_label, get_explore_parents
from program_management.business.utils import html2text
from program_management.forms.custom_xls import CustomXlsForm
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
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
CMS_TXT_WITH_LINK_AFTER_FORMATTING = 'moodle - [https://moodleucl.uclouvain.be] \n'


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

    def test_header_lines_without_optional_titles(self):
        custom_xls_form = CustomXlsForm({})
        expected_headers = FIX_TITLES

        self.assertListEqual(_get_headers(custom_xls_form)[0], expected_headers)

    def test_header_lines_with_optional_titles(self):
        custom_xls_form = CustomXlsForm({
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
        }
        )

        expected_headers = \
            FIX_TITLES + optional_header_for_required_entity + optional_header_for_allocation_entity + \
            optional_header_for_credits + optional_header_for_periodicity + optional_header_for_active + \
            optional_header_for_quadrimester + optional_header_for_session_derogation + optional_header_for_volume + \
            optional_header_for_teacher_list + optional_header_for_proposition + optional_header_for_english_title + \
            optional_header_for_language + optional_header_for_specifications + optional_header_for_description_fiche
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
        cls.child_node = NodeGroupYearFactory()
        cls.lu = NodeLearningUnitYearFactory()

        cls.link_1 = LinkFactory(parent=cls.parent_node, child=cls.child_node, is_mandatory=True)
        cls.link_1_1 = LinkFactory(parent=cls.child_node, child=cls.lu, is_mandatory=True)

        cls.ue_entities = EntitiesFactory(requirement_entity_acronym='ILV', allocation_entity_acronym='DRT')

        cls.teacher_1 = TeacherFactory(last_name='Dupont', first_name="Marcel", email="dm@gmail.com")
        cls.attribution_1 = Attribution(teacher=cls.teacher_1)
        cls.teacher_2 = TeacherFactory(last_name='Marseillais', first_name="Pol", email="pm@gmail.com")

        cls.attribution_2 = Attribution(teacher=cls.teacher_2)

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
        )

    def test_fix_data(self):
        expected = get_expected_data_new(self.child_node, self.luy, self.link_1_1, self.link_1.parent)
        res = _fix_data(self.link_1_1,
                        self.luy,
                        {
                            DIRECT_GATHERING_KEY: self.child_node,
                            MAIN_GATHERING_KEY: self.parent_node,
                            EXCLUDE_UE_KEY: False
                        })
        self.assertEqual(res, expected)

    def test_no_main_parent_result(self):
        root_node = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        link = LinkFactory(parent=root_node)
        root_node = link.parent

        # ProgramTreeFactory(root_node=root_node)

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
        form = CustomXlsForm({})
        self.assertDictEqual(_optional_data(form),
                             {'has_required_entity': False,
                              'has_proposition': False,
                              'has_credits': False,
                              'has_allocation_entity': False,
                              'has_english_title': False,
                              'has_teacher_list': False,
                              'has_periodicity': False,
                              'has_active': False,
                              'has_volume': False,
                              'has_quadrimester': False,
                              'has_session_derogation': False,
                              'has_language': False,
                              'has_description_fiche': False,
                              'has_specifications': False,
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
                              })
        self.assertDictEqual(_optional_data(form),
                             {'has_required_entity': True,
                              'has_proposition': True,
                              'has_credits': True,
                              'has_allocation_entity': True,
                              'has_english_title': True,
                              'has_teacher_list': True,
                              'has_periodicity': True,
                              'has_active': True,
                              'has_volume': True,
                              'has_quadrimester': True,
                              'has_session_derogation': True,
                              'has_language': True,
                              'has_description_fiche': True,
                              'has_specifications': True,
                              }
                             )

    def test_get_optional_required_entity(self):
        optional_data = initialize_optional_data()
        optional_data['has_required_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.entities.requirement_entity_acronym])

    def test_get_optional_allocation_entity(self):
        optional_data = initialize_optional_data()
        optional_data['has_allocation_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.entities.allocation_entity_acronym])

    def test_get_optional_credits(self):
        optional_data = initialize_optional_data()
        optional_data['has_credits'] = True

        self.assertCountEqual(
            _get_optional_data([], self.luy, optional_data, self.link_1_1),
            [self.link_1_1.relative_credits or '-', self.luy.credits.to_integral_value() or '-']
        )

    def test_get_optional_has_periodicity(self):
        optional_data = initialize_optional_data()
        optional_data['has_periodicity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.periodicity])

    def test_get_optional_has_active(self):
        optional_data = initialize_optional_data()
        optional_data['has_active'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [_('yes')])

    def test_get_optional_has_quadrimester(self):
        optional_data = initialize_optional_data()
        optional_data['has_quadrimester'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.quadrimester or ''])

    def test_get_optional_has_session_derogation(self):
        optional_data = initialize_optional_data()
        optional_data['has_session_derogation'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.session or ''])

    def test_get_optional_has_proposition(self):
        optional_data = initialize_optional_data()
        optional_data['has_proposition'] = True
        luy_without_proposition = DddLearningUnitYearFactory(proposal=None)
        self.assertCountEqual(_get_optional_data([], luy_without_proposition, optional_data, self.link_1_1),
                              ['', ''])
        proposal = ProposalFactory()
        self.luy.proposal = proposal
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [ProposalType.get_value(self.luy.proposal.type),
                               ProposalState.get_value(self.luy.proposal.state)])

    def test_get_optional_has_english_title(self):
        optional_data = initialize_optional_data()
        optional_data['has_english_title'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.full_title_en])

    def test_get_optional_has_language(self):
        optional_data = initialize_optional_data()
        optional_data['has_language'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.link_1_1),
                              [self.luy.main_language])

    def test_get_optional_has_teacher_list(self):
        optional_data = initialize_optional_data()
        optional_data['has_teacher_list'] = True
        teacher_data = _get_optional_data([], self.luy, optional_data, self.link_1_1)
        self.assertEqual(teacher_data[0], "{} {};{} {}"
                         .format(self.teacher_1.last_name.upper(), self.teacher_1.first_name,
                                 self.teacher_2.last_name.upper(), self.teacher_2.first_name))
        self.assertEqual(teacher_data[1], "{};{}"
                         .format(self.teacher_1.email,
                                 self.teacher_2.email))

    def test_build_description_fiche_cols(self):
        teaching_material_1 = DddTeachingMaterialFactory(title='Title mandatory', is_mandatory=True)
        teaching_material_2 = DddTeachingMaterialFactory(title='Title non-mandatory', is_mandatory=False)

        ue_description_fiche = _initialize_cms_data_description_fiche()

        description_fiche = _build_description_fiche_cols(ue_description_fiche,
                                                          [teaching_material_1, teaching_material_2])

        self.assertEqual(description_fiche.resume, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.resume_en, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.teaching_methods, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.teaching_methods_en, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.evaluation_methods, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.evaluation_methods_en, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.other_informations, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.other_informations_en, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.mobility, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))
        self.assertEqual(description_fiche.bibliography, "{}".format(CMS_TXT_WITH_LIST_AFTER_FORMATTING))

        self.assertEqual(description_fiche.online_resources, "{}".format(CMS_TXT_WITH_LINK_AFTER_FORMATTING))
        self.assertEqual(description_fiche.online_resources_en, "{}".format(CMS_TXT_WITH_LINK_AFTER_FORMATTING))

        self.assertEqual(description_fiche.teaching_materials,
                         "{} - {}\n{} - {}".format(_('Mandatory'),
                                                   teaching_material_1.title,
                                                   _('Non-mandatory'),
                                                   teaching_material_2.title))

    def test_build_specifications_cols(self):
        # lang_fr = FrenchLanguageFactory()
        # lang_en = EnglishLanguageFactory()

        achievement_1 = AchievementFactory(code_name="A1", text_fr="Text fr", text_en="Text en")
        achievement_2 = AchievementFactory(code_name="A2", text_fr="Text fr", text_en=None)
        achievement_3 = AchievementFactory(code_name="A3", text_fr=None, text_en="    ")
        achievement_4 = AchievementFactory(code_name=None, text_fr=None, text_en="    ")

        specifications = initialize_cms_specifications_data_description_fiche()
        specifications_data = _build_specifications_cols([achievement_1, achievement_2, achievement_3, achievement_4],
                                                         specifications)

        self.assertEqual(specifications_data.prerequisite, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.prerequisite_en, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.themes_discussed, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.themes_discussed_en, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.achievements_fr, "{} -{}\n{} -{}".format(
            achievement_1.code_name, achievement_1.text_fr,
            achievement_2.code_name, achievement_2.text_fr)
                         )
        self.assertEqual(specifications_data.achievements_en, "{} -{}".format(
            achievement_1.code_name, achievement_1.text_en)
                         )

    def test_build_validate_html_list_to_string(self):
        self.assertEqual(_build_validate_html_list_to_string(None, html2text), "")

    def test_build_validate_html_list_to_string_illegal_character(self):
        self.assertEqual(_build_validate_html_list_to_string("", html2text),
                         "!!! {}".format(_('IMPOSSIBLE TO DISPLAY BECAUSE OF AN ILLEGAL CHARACTER IN STRING')))

    def test_build_validate_html_list_to_string_wrong_method(self):
        self.assertEqual(_build_validate_html_list_to_string('Test', None), 'Test')

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
        self.assertEqual(_build_main_gathering_label(edg_finality),
                         "{} - {}".format(edg_finality.title, edg_finality.offer_partial_title_fr))

    def test_build_main_gathering_label_not_master(self):
        node_not_finality = NodeGroupYearFactory(node_type=GroupType.COMMON_CORE)
        self.assertEqual(_build_main_gathering_label(node_not_finality),
                         "{} - {}".format(node_not_finality.title, node_not_finality.group_title_fr))


class TestExcludeUEFromdWorkbook(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = TrainingFactory(
            acronym='DROI2M',
            education_group_type__name=education_group_types.TrainingType.PGRM_MASTER_120.name
        )
        academic_year = cls.root.academic_year
        finality_list = GroupFactory(
            acronym='LIST FINALITIES',
            education_group_type__name=education_group_types.GroupType.FINALITY_120_LIST_CHOICE.name,
            academic_year=academic_year
        )

        cls.formation_master_md = TrainingFactory(
            acronym='DROI2MD',
            education_group_type__name=education_group_types.TrainingType.MASTER_MD_120.name,
            academic_year=academic_year
        )

        common_core = GroupFactory(
            acronym='TC DROI2MD',
            education_group_type__name=education_group_types.GroupType.COMMON_CORE.name,
            academic_year=academic_year
        )
        options = GroupFactory(
            acronym='TC DROI2MD',
            education_group_type__name=education_group_types.GroupType.OPTION_LIST_CHOICE.name,
            academic_year=academic_year
        )

        cls.luy_in_common_core = LearningUnitYearFactory()
        cls.luy_in_finality_options = LearningUnitYearFactory()

        GroupElementYearFactory(parent=cls.root, child_branch=finality_list, child_leaf=None)
        GroupElementYearFactory(parent=finality_list, child_branch=cls.formation_master_md, child_leaf=None)
        GroupElementYearFactory(parent=cls.formation_master_md, child_branch=common_core, child_leaf=None)
        GroupElementYearFactory(parent=cls.formation_master_md, child_branch=options, child_leaf=None)
        GroupElementYearFactory(parent=common_core,
                                child_leaf=cls.luy_in_common_core,
                                child_branch=None)
        GroupElementYearFactory(parent=options,
                                child_leaf=cls.luy_in_finality_options,
                                child_branch=None)


def get_expected_data(gey, luy, main_gathering=None):
    gathering_str = "{} - {}".format(gey.parent.partial_acronym, gey.parent.title)
    if main_gathering:
        main_gathering_str = "{} - {}".format(main_gathering.acronym, main_gathering.title)
    else:
        main_gathering_str = gathering_str
    expected = [luy.acronym,
                luy.academic_year,
                luy.complete_title_i18n,
                luy.get_container_type_display(),
                luy.get_subtype_display(),
                gathering_str,
                main_gathering_str,
                gey.block or '',
                _('yes')

                ]
    return expected


def initialize_optional_data():
    return {
        'has_required_entity': False,
        'has_allocation_entity': False,
        'has_credits': False,
        'has_periodicity': False,
        'has_active': False,
        'has_quadrimester': False,
        'has_session_derogation': False,
        'has_volume': False,
        'has_teacher_list': False,
        'has_proposition': False,
        'has_english_title': False,
        'has_language': False,
        'has_description_fiche': False,
        'has_specifications': False,
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
            else main_gathering.group_title_fr) if main_gathering else ''
    else:
        main_gathering_str = ''

    expected = [luy.acronym,
                luy.year,
                luy.full_title_fr,
                luy.type.value if luy.type else '',
                luy.subtype if luy.subtype else '',
                gathering_str,
                main_gathering_str,
                link.block or '',
                _('yes')
                ]
    return expected


class TestRowHeight(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.root_node = NodeGroupYearFactory(node_id=1, code='c1', node_type=TrainingType.PGRM_MASTER_120)
        cls.academic_year = AcademicYearFactory(year=cls.root_node.year)
        cls.group_level_1 = NodeGroupYearFactory(node_id=2, code='c2', year=cls.academic_year.year)
        LinkFactory(parent=cls.root_node,
                    child=cls.group_level_1)

        cls.group_level_1_1 = NodeGroupYearFactory(node_id=3, code='c3', year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_1,
                    child=cls.group_level_1_1)

        cls.ue_level_group_level_1_1 = NodeLearningUnitYearFactory(node_id=4, code='ue1', year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_1_1,
                    child=cls.ue_level_group_level_1_1)
        second_ue_level_group_level_1_1 = NodeLearningUnitYearFactory(node_id=5,
                                                                      code='ue2',
                                                                      year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_1_1,
                    child=second_ue_level_group_level_1_1)

        cls.group_level_2 = NodeGroupYearFactory(node_id=6,
                                                 node_type=TrainingType.MASTER_MS_120,
                                                 year=cls.academic_year.year)
        LinkFactory(parent=cls.root_node,
                    child=cls.group_level_2)

        cls.group_level_2_1 = NodeGroupYearFactory(node_id=7,
                                                   node_type=GroupType.COMMON_CORE,
                                                   year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_2,
                    child=cls.group_level_2_1)
        cls.ue_level_group_level_2_1 = NodeLearningUnitYearFactory(node_id=9, code='ue3', year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_2_1,
                    child=cls.ue_level_group_level_2_1)
        cls.group_level_2_2 = NodeGroupYearFactory(node_id=8,
                                                   node_type=GroupType.OPTION_LIST_CHOICE,
                                                   year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_2,
                    child=cls.group_level_2_2)
        cls.ue_level_group_level_2_2 = NodeLearningUnitYearFactory(node_id=10, year=cls.academic_year.year)
        LinkFactory(parent=cls.group_level_2_2,
                    child=cls.ue_level_group_level_2_2)

        cls.tree = ProgramTreeFactory(root_node=cls.root_node)

        # TODO : remplacer ce qui suit pour un accès plus direct

        element_ue_1 = ElementLearningUnitYearFactory(id=cls.ue_level_group_level_1_1.node_id,
                                                      learning_unit_year=LearningUnitYearFactory(
                                                          acronym='ue1', academic_year=cls.academic_year)
                                                      )
        element_ue_2 = ElementLearningUnitYearFactory(id=second_ue_level_group_level_1_1.node_id,
                                                      learning_unit_year=LearningUnitYearFactory(
                                                          acronym='ue2', academic_year=cls.academic_year)
                                                      )
        element_ue_3 = ElementLearningUnitYearFactory(id=cls.ue_level_group_level_2_1.node_id,
                                                      learning_unit_year=LearningUnitYearFactory(
                                                          acronym='ue3', academic_year=cls.academic_year)
                                                      )
        ElementLearningUnitYearFactory(id=cls.ue_level_group_level_2_2.node_id,
                                       learning_unit_year=LearningUnitYearFactory(academic_year=cls.academic_year))

        cls.learning_units = [element_ue_1.learning_unit_year, element_ue_2.learning_unit_year,
                              element_ue_3.learning_unit_year]
        cls.luy_count = len(cls.learning_units)

    def test_row_height_not_populated(self):
        custom_form = CustomXlsForm({})
        data = _build_excel_lines_ues(custom_form, self.tree)
        self.assertDictEqual(data.get('row_height'), {})

    def test_row_height_populated(self):
        custom_form = CustomXlsForm({'description_fiche': 'on'})
        data = _build_excel_lines_ues(custom_form, self.tree)

        self.assertDictEqual(data.get('row_height'), {
            'height': 30,
            'start': 2,
            'stop': self.luy_count + 2
        })

    def test_header_line(self):
        custom_form = CustomXlsForm({})
        data = _build_excel_lines_ues(custom_form, self.tree)
        # First line (Header line) is always bold
        self.assertListEqual(data.get('font_rows')[BOLD_FONT], [0])

    def test_exclude_options_list_for_2M(self):
        self._assert_correct_ue_present_in_xls2(self.tree, ['ue1', 'ue2', 'ue3'])

    def test_do_not_exclude_options_list_if_not_2M(self):
        bachelor_root_node = NodeGroupYearFactory(node_type=TrainingType.BACHELOR, year=self.academic_year.year)

        group_level_1 = NodeGroupYearFactory(year=self.academic_year.year)
        LinkFactory(parent=bachelor_root_node,
                    child=group_level_1)

        group_level_1_1 = NodeGroupYearFactory(year=self.academic_year.year)
        LinkFactory(parent=group_level_1,
                    child=group_level_1_1)

        ue_level_group_level_1_1 = NodeLearningUnitYearFactory(code='ue21', node_id=100, year=self.academic_year.year)
        LinkFactory(parent=group_level_1_1,
                    child=ue_level_group_level_1_1)
        second_ue_level_group_level_1_1 = NodeLearningUnitYearFactory(code='ue22',
                                                                      node_id=101,
                                                                      year=self.academic_year.year)
        LinkFactory(parent=group_level_1_1,
                    child=second_ue_level_group_level_1_1)

        group_level_2 = NodeGroupYearFactory(node_id=6,
                                             node_type=GroupType.OPTION_LIST_CHOICE,
                                             year=self.academic_year.year)
        LinkFactory(parent=bachelor_root_node,
                    child=group_level_2)

        ue_level_group_level_2 = NodeLearningUnitYearFactory(code='ue23', node_id=102, year=self.academic_year.year)
        LinkFactory(parent=group_level_2,
                    child=ue_level_group_level_2)
        bachelor_tree = ProgramTreeFactory(root_node=bachelor_root_node)
        # TODO : remplacer ce qui suit pour un accès plus direct
        ElementLearningUnitYearFactory(id=ue_level_group_level_1_1.node_id,
                                       learning_unit_year=LearningUnitYearFactory(acronym='ue21',
                                                                                  academic_year=self.academic_year))
        ElementLearningUnitYearFactory(id=second_ue_level_group_level_1_1.node_id,
                                       learning_unit_year=LearningUnitYearFactory(
                                           acronym='ue22',
                                           academic_year=self.academic_year
                                       )
                                       )
        ElementLearningUnitYearFactory(id=ue_level_group_level_2.node_id,
                                       learning_unit_year=LearningUnitYearFactory(acronym='ue23',
                                                                                  academic_year=self.academic_year)
                                       )

        self._assert_correct_ue_present_in_xls2(bachelor_tree, ['ue21', 'ue22', 'ue23'])

    def _assert_correct_ue_present_in_xls2(self, tree, ues):
        data = _build_excel_lines_ues(CustomXlsForm({}), tree)
        content = data['content']
        del content[0]
        self.assertEqual(len(content), len(ues))
        self.assertCountEqual([content[0][0], content[1][0],
                               content[2][0]], ues)
