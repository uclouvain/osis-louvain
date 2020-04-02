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
import random
from unittest import mock

from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from openpyxl.styles import Style, Font

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business.learning_unit_xls import CREATION_COLOR, MODIFICATION_COLOR, TRANSFORMATION_COLOR, \
    TRANSFORMATION_AND_MODIFICATION_COLOR, SUPPRESSION_COLOR
from base.models.enums import education_group_types
from base.models.enums.education_group_types import GroupType, TrainingType
from base.models.enums.education_group_categories import Categories
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.education_group_year import EducationGroupYearFactory, GroupFactory, TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearChildLeafFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_component_year import LecturingLearningComponentYearFactory, \
    PracticalLearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.tutor import TutorFactory
from program_management.business.excel import _get_blocks_prerequisite_of
from program_management.business.excel_ue_in_of import EducationGroupYearLearningUnitsContainedToExcel, FIX_TITLES, \
    _get_headers, optional_header_for_proposition, optional_header_for_credits, optional_header_for_volume, \
    _get_attribution_line, optional_header_for_required_entity, optional_header_for_active, \
    optional_header_for_allocation_entity, optional_header_for_description_fiche, optional_header_for_english_title, \
    optional_header_for_language, optional_header_for_periodicity, optional_header_for_quadrimester, \
    optional_header_for_session_derogation, optional_header_for_specifications, optional_header_for_teacher_list, \
    _fix_data, _get_workbook_for_custom_xls, _build_legend_sheet, LEGEND_WB_CONTENT, LEGEND_WB_STYLE, _optional_data, \
    _build_excel_lines_ues, _get_optional_data, BOLD_FONT, _build_specifications_cols, _build_description_fiche_cols, \
    _build_validate_html_list_to_string, _build_gathering_content, _build_main_gathering_content
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.business.utils import html2text
from program_management.forms.custom_xls import CustomXlsForm
from reference.tests.factories.language import LanguageFactory

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
        cls.education_group_yr_root = TrainingFactory(acronym='root')
        academic_yr = cls.education_group_yr_root.academic_year
        cls.child_leaves = GroupElementYearChildLeafFactory.create_batch(
            2,
            parent=cls.education_group_yr_root,
            is_mandatory=True
        )
        for node, acronym in zip(cls.child_leaves, ["LCORS124" + str(i) for i in range(0, len(cls.child_leaves))]):
            node.child_leaf.acronym = acronym
            node.child_leaf.save()
        cls.edy_node_1_training = TrainingFactory(academic_year=academic_yr,
                                                  education_group_type__category=Categories.TRAINING.name,
                                                  partial_acronym="{}_T".format(PARTIAL_ACRONYM),
                                                  title="{}_T".format(TITLE))
        cls.node_1 = GroupElementYearFactory(
            child_branch=cls.edy_node_1_training, child_leaf=None, parent=cls.education_group_yr_root
        )
        cls.edy_node_1_1_group = EducationGroupYearFactory(academic_year=academic_yr,
                                                           education_group_type__category=Categories.GROUP.name)

        cls.node_1_1 = GroupElementYearFactory(child_branch=cls.edy_node_1_1_group,
                                               child_leaf=None,
                                               parent=cls.edy_node_1_training)
        cls.child_leave_node_11 = GroupElementYearChildLeafFactory(
            parent=cls.edy_node_1_1_group, is_mandatory=True
        )
        cls.edy_node_1_1_1_group_type = EducationGroupYearFactory(academic_year=academic_yr,
                                                                  education_group_type__category=Categories.GROUP.name)

        cls.node_1_1_1_group = GroupElementYearFactory(child_branch=cls.edy_node_1_1_1_group_type, child_leaf=None,
                                                       parent=cls.edy_node_1_1_group)
        cls.child_leave_node_111 = GroupElementYearChildLeafFactory(
            parent=cls.edy_node_1_1_1_group_type, is_mandatory=True
        )

        cls.luy_children_in_tree = [child.child_leaf for child in cls.child_leaves]
        cls.luy_children_in_tree.append(cls.child_leave_node_11.child_leaf)
        cls.luy_children_with_direct_gathering = cls.luy_children_in_tree.copy()
        cls.luy_children_in_tree.append(cls.child_leave_node_111.child_leaf)

        cls.workbook_contains = \
            EducationGroupYearLearningUnitsContainedToExcel(cls.education_group_yr_root,
                                                            cls.education_group_yr_root,
                                                            CustomXlsForm({}))._to_workbook()
        cls.sheet_contains = cls.workbook_contains.worksheets[0]

        generator_container = GenerateContainer(cls.education_group_yr_root.academic_year,
                                                cls.education_group_yr_root.academic_year)
        cls.luy = generator_container.generated_container_years[0].learning_unit_year_full

        cls.lecturing_component = LecturingLearningComponentYearFactory(
            learning_unit_year=cls.luy)
        cls.practical_component = PracticalLearningComponentYearFactory(
            learning_unit_year=cls.luy)
        cls.person_1 = PersonFactory(last_name='Dupont', first_name="Marcel", email="dm@gmail.com")
        cls.person_2 = PersonFactory(last_name='Marseillais', first_name="Pol", email="pm@gmail.com")
        cls.tutor_1 = TutorFactory(person=cls.person_1)
        cls.tutor_2 = TutorFactory(person=cls.person_2)
        cls.attribution_1 = AttributionNewFactory(
            tutor=cls.tutor_1,
            learning_container_year=cls.luy.learning_container_year
        )
        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution_1,
            learning_component_year=cls.lecturing_component
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution_1,
            learning_component_year=cls.practical_component
        )
        cls.attribution_2 = AttributionNewFactory(
            tutor=cls.tutor_2,
            learning_container_year=cls.luy.learning_container_year
        )
        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution_2,
            learning_component_year=cls.lecturing_component
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution_2,
            learning_component_year=cls.practical_component
        )
        cls.gey = GroupElementYearChildLeafFactory(
            child_leaf=cls.luy
        )
        cls.hierarchy = EducationGroupHierarchy(root=cls.education_group_yr_root)

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
            FIX_TITLES + optional_header_for_required_entity + optional_header_for_allocation_entity +  \
            optional_header_for_credits + optional_header_for_periodicity + optional_header_for_active + \
            optional_header_for_quadrimester + optional_header_for_session_derogation + optional_header_for_volume + \
            optional_header_for_teacher_list + optional_header_for_proposition + optional_header_for_english_title + \
            optional_header_for_language + optional_header_for_specifications + optional_header_for_description_fiche
        self.assertListEqual(_get_headers(custom_xls_form)[0], expected_headers)

    def test_get_attribution_line(self):
        person = PersonFactory(last_name='Last', first_name='First', middle_name='Middle')
        self.assertEqual(_get_attribution_line(person), 'LAST First Middle')
        person = PersonFactory(last_name=None, first_name='First', middle_name='Middle')
        self.assertEqual(_get_attribution_line(person), 'First Middle')
        self.assertEqual(_get_attribution_line(None), '')

    def test_fix_data(self):
        gey = self.child_leaves[0]
        luy = self.luy_children_in_tree[0]
        expected = get_expected_data(gey, luy, self.education_group_yr_root)
        res = _fix_data(gey, luy, self.hierarchy)
        self.assertEqual(res, expected)

    def test_main_parent_result(self):
        #  To find main gathering loop up through the hierarchy till you find
        #  complementary module/formation/mini-formation
        self.assertEqual(self.hierarchy.get_main_parent(self.education_group_yr_root.id), self.education_group_yr_root)
        self.assertEqual(self.hierarchy.get_main_parent(self.edy_node_1_training.id), self.edy_node_1_training)
        self.assertEqual(self.hierarchy.get_main_parent(self.edy_node_1_1_group.id), self.edy_node_1_training)

    def test_main_parent_result_not_direct_parent(self):
        self.assertEqual(self.hierarchy.get_main_parent(self.edy_node_1_1_1_group_type.id), self.edy_node_1_training)

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
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Style(font=Font(color=CREATION_COLOR))), [1])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Style(font=Font(color=MODIFICATION_COLOR))), [2])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Style(font=Font(color=TRANSFORMATION_COLOR))), [3])
        self.assertListEqual(
            data.get(LEGEND_WB_STYLE).get(Style(font=Font(color=TRANSFORMATION_AND_MODIFICATION_COLOR))),
            [4])
        self.assertListEqual(data.get(LEGEND_WB_STYLE).get(Style(font=Font(color=SUPPRESSION_COLOR))), [5])

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

    def test_data(self):
        custom_form = CustomXlsForm({})
        exl = EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                              self.education_group_yr_root,
                                                              custom_form)
        data = _build_excel_lines_ues(custom_form, exl.learning_unit_years_parent, self.hierarchy)
        content = data.get('content')
        self._assert_content_equals(content, exl)
        # First line (Header line) is always bold
        self.assertListEqual(data.get('colored_cells')[Style(font=BOLD_FONT)], [0])

    def _assert_content_equals(self, content, exl):
        idx = 1
        for gey in exl.learning_unit_years_parent:
            luy = gey.child_leaf
            if luy != self.child_leave_node_111.child_leaf and luy != self.child_leave_node_11.child_leaf:
                expected = get_expected_data(gey, luy, gey.parent)
            else:
                # main_gathering different than direct parent
                expected = get_expected_data(gey, luy, self.edy_node_1_training)
            self.assertListEqual(content[idx], expected)
            idx += 1

    def test_get_optional_required_entity(self):
        optional_data = initialize_optional_data()
        optional_data['has_required_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.learning_container_year.requirement_entity])

    def test_get_optional_allocation_entity(self):
        optional_data = initialize_optional_data()
        optional_data['has_allocation_entity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.learning_container_year.allocation_entity])

    def test_get_optional_credits(self):
        optional_data = initialize_optional_data()
        optional_data['has_credits'] = True

        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.gey.relative_credits or '-', self.luy.credits.to_integral_value()])

    def test_get_optional_has_periodicity(self):
        optional_data = initialize_optional_data()
        optional_data['has_periodicity'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.get_periodicity_display()])

    def test_get_optional_has_active(self):
        optional_data = initialize_optional_data()
        optional_data['has_active'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [_('yes')])

    def test_get_optional_has_quadrimester(self):
        optional_data = initialize_optional_data()
        optional_data['has_quadrimester'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.get_quadrimester_display() or ''])

    def test_get_optional_has_session_derogation(self):
        optional_data = initialize_optional_data()
        optional_data['has_session_derogation'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.get_session_display() or ''])

    def test_get_optional_has_proposition(self):
        optional_data = initialize_optional_data()
        optional_data['has_proposition'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              ['', ''])
        proposal = ProposalLearningUnitFactory(learning_unit_year=self.luy)

        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [proposal.get_type_display(), proposal.get_state_display()])

    def test_get_optional_has_english_title(self):
        optional_data = initialize_optional_data()
        optional_data['has_english_title'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.complete_title_english])

    def test_get_optional_has_language(self):
        optional_data = initialize_optional_data()
        optional_data['has_language'] = True
        self.assertCountEqual(_get_optional_data([], self.luy, optional_data, self.gey),
                              [self.luy.language])

    def test_get_optional_has_teacher_list(self):
        optional_data = initialize_optional_data()
        optional_data['has_teacher_list'] = True
        teacher_data = _get_optional_data([], self.luy, optional_data, self.gey)
        self.assertEqual(teacher_data[0], "{} {};{} {}"
                         .format(self.person_1.last_name.upper(), self.person_1.first_name,
                                 self.person_2.last_name.upper(), self.person_2.first_name))
        self.assertEqual(teacher_data[1], "{};{}"
                         .format(self.person_1.email,
                                 self.person_2.email))

    @mock.patch("program_management.business.excel_ue_in_of._annotate_with_description_fiche_specifications")
    def test_get_optional_has_description_fiche_annotate_called(self, mock):
        optional_data = initialize_optional_data()
        optional_data['has_description_fiche'] = True

        custom_form = CustomXlsForm({'description_fiche': 'on'})
        EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                        self.education_group_yr_root,
                                                        custom_form)
        self.assertTrue(mock.called)

    @mock.patch("program_management.business.excel_ue_in_of._annotate_with_description_fiche_specifications")
    def test_get_optional_has_specifications_annotate_called(self, mock):
        optional_data = initialize_optional_data()
        optional_data['has_specifications'] = True

        custom_form = CustomXlsForm({'specifications': 'on'})
        EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                        self.education_group_yr_root,
                                                        custom_form)
        self.assertTrue(mock.called)

    def test_build_description_fiche_cols(self):

        teaching_material_1 = TeachingMaterialFactory(
            learning_unit_year=self.luy, title='Title mandatory', mandatory=True
        )
        teaching_material_2 = TeachingMaterialFactory(
            learning_unit_year=self.luy, title='Title non-mandatory', mandatory=False
        )

        _initialize_cms_data_description_fiche(self.gey)

        description_fiche = _build_description_fiche_cols(self.luy, self.gey)

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

        lang_fr = LanguageFactory(code='FR')
        lang_en = LanguageFactory(code='EN')

        achievement_1_fr = LearningAchievementFactory(learning_unit_year=self.luy, language=lang_fr)
        achievement_2_fr = LearningAchievementFactory(learning_unit_year=self.luy, language=lang_fr)
        achievement_1_en = LearningAchievementFactory(learning_unit_year=self.luy, language=lang_en)
        LearningAchievementFactory(learning_unit_year=self.luy, language=lang_en, text="    ")
        LearningAchievementFactory(learning_unit_year=self.luy, language=lang_en, text="    ", code_name=None)

        initialize_cms_specifications_data_description_fiche(self.gey)
        specifications_data = _build_specifications_cols(self.luy, self.gey)

        self.assertEqual(specifications_data.prerequisite, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.prerequisite_en, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.themes_discussed, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.themes_discussed_en, CMS_TXT_WITH_LIST_AFTER_FORMATTING)
        self.assertEqual(specifications_data.achievements_fr, "{} -{}\n{} -{}".format(
            achievement_1_fr.code_name, achievement_1_fr.text,
            achievement_2_fr.code_name, achievement_2_fr.text)
                         )
        self.assertEqual(specifications_data.achievements_en, "{} -{}".format(
            achievement_1_en.code_name, achievement_1_en.text)
                         )

    def test_build_validate_html_list_to_string(self):
        self.assertEqual(_build_validate_html_list_to_string(None, html2text), "")

    def test_build_validate_html_list_to_string_illegal_character(self):
        self.assertEqual(_build_validate_html_list_to_string("", html2text),
                         "!!! {}".format(_('IMPOSSIBLE TO DISPLAY BECAUSE OF AN ILLEGAL CHARACTER IN STRING')))

    def test_build_validate_html_list_to_string_wrong_method(self):
        self.assertEqual(_build_validate_html_list_to_string('Test', None), 'Test')
        self.assertEqual(_build_validate_html_list_to_string('Test', _get_blocks_prerequisite_of), 'Test')

    def test_row_height_not_populated(self):
        custom_form = CustomXlsForm({})
        exl = EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                              self.education_group_yr_root,
                                                              custom_form)
        data = _build_excel_lines_ues(custom_form, exl.qs, self.hierarchy)
        self.assertDictEqual(data.get('row_height'), {})

    def test_row_height_populated(self):
        custom_form = CustomXlsForm({'description_fiche': 'on'})
        exl = EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                              self.education_group_yr_root,
                                                              custom_form)
        data = _build_excel_lines_ues(custom_form, exl.qs, self.hierarchy)
        self.assertDictEqual(data.get('row_height'), {
            'height': 30,
            'start': 2,
            'stop': len(self.luy_children_in_tree) + 2
        })

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

    def test_keep_UES_tree_order_in_qs(self):
        exl = EducationGroupYearLearningUnitsContainedToExcel(self.education_group_yr_root,
                                                              self.education_group_yr_root,
                                                              CustomXlsForm({}))
        expected_ids_following_tree_order = [lu.id for lu in exl.learning_unit_years_parent]
        ids_ordered_for_xls = [lu.id for lu in list(exl.qs)]
        self.assertCountEqual(expected_ids_following_tree_order, ids_ordered_for_xls)

    def test_build_gathering_content(self):
        self.assertEqual(_build_gathering_content(None), '')
        self.assertEqual(_build_gathering_content(self.education_group_yr_root),
                         "{} - {}".format(self.education_group_yr_root.partial_acronym,
                                          self.education_group_yr_root.title))

    def test_build_main_gathering_content_finality_master(self):
        edg_finality = EducationGroupYearFactory(
            education_group_type__name=random.choice(TrainingType.finality_types()),
            partial_title='partial_title')
        self.assertEqual(_build_main_gathering_content(edg_finality),
                         "{} - {}".format(edg_finality.acronym, edg_finality.partial_title))

    def test_build_main_gathering_content_not_master(self):
        edg_not_a_finality = EducationGroupYearFactory(education_group_type__name=GroupType.COMMON_CORE.name)
        self.assertEqual(_build_main_gathering_content(edg_not_a_finality),
                         "{} - {}".format(edg_not_a_finality.acronym, edg_not_a_finality.title))


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

    def test_exclude_options_list_for_2M(self):
        self._assert_correct_ue_present_in_xls(self.root, [self.luy_in_common_core.id])

    def test_do_not_exclude_options_list_if_not_2M(self):
        self._assert_correct_ue_present_in_xls(self.formation_master_md,
                                               [self.luy_in_common_core.id, self.luy_in_finality_options.id])

    def _assert_correct_ue_present_in_xls(self, edy, expected_ue_ids_in_xls):
        exl = EducationGroupYearLearningUnitsContainedToExcel(edy, edy, CustomXlsForm({}))
        ue_ids_in_xls = [lu.child_leaf.id for lu in list(exl.qs)]
        self.assertCountEqual(expected_ue_ids_in_xls, ue_ids_in_xls)


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


def _initialize_cms_data_description_fiche(gey):
    gey_cms = gey
    gey_cms.resume = CMS_TXT_WITH_LIST
    gey_cms.resume_en = CMS_TXT_WITH_LIST
    gey_cms.teaching_methods = CMS_TXT_WITH_LIST
    gey_cms.teaching_methods_en = CMS_TXT_WITH_LIST
    gey_cms.evaluation_methods = CMS_TXT_WITH_LIST
    gey_cms.evaluation_methods_en = CMS_TXT_WITH_LIST
    gey_cms.other_informations = CMS_TXT_WITH_LIST
    gey_cms.other_informations_en = CMS_TXT_WITH_LIST
    gey_cms.bibliography = CMS_TXT_WITH_LIST
    gey_cms.mobility = CMS_TXT_WITH_LIST

    gey_cms.online_resources = CMS_TXT_WITH_LINK
    gey_cms.online_resources_en = CMS_TXT_WITH_LINK

    return gey_cms


def initialize_cms_specifications_data_description_fiche(gey):
    gey_cms = gey
    gey_cms.prerequisite = CMS_TXT_WITH_LIST
    gey_cms.prerequisite_en = CMS_TXT_WITH_LIST
    gey_cms.themes_discussed = CMS_TXT_WITH_LIST
    gey_cms.themes_discussed_en = CMS_TXT_WITH_LIST
    return gey_cms
