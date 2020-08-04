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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.db.models.expressions import RawSQL, Subquery, OuterRef
from django.template.defaultfilters import yesno
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from attribution.business import attribution_charge_new
from attribution.models.enums.function import COORDINATOR
from attribution.models.enums.function import Functions
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business.learning_unit_xls import DEFAULT_LEGEND_FILLS, SPACES, PROPOSAL_LINE_STYLES, \
    prepare_proposal_legend_ws_data, _get_wrapped_cells, \
    _get_font_rows, _get_attribution_line, _add_training_data, \
    _get_data_part1, _get_parameters_configurable_list, WRAP_TEXT_ALIGNMENT, HEADER_PROGRAMS, XLS_DESCRIPTION, \
    _get_data_part2, annotate_qs, learning_unit_titles_part1, prepare_xls_content, _get_attribution_detail, \
    prepare_xls_content_with_attributions
from base.business.learning_unit_xls import _get_col_letter
from base.business.learning_unit_xls import get_significant_volume
from base.models.entity_version import EntityVersion
from base.models.enums import education_group_categories
from base.models.enums import entity_type, organization_type
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_periodicity
from base.models.enums import proposal_type, proposal_state
from base.models.learning_unit_year import LearningUnitYear, SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory
from education_group.tests.factories.group_year import GroupYearFactory
from osis_common.document import xls_build
from program_management.tests.factories.education_group_version import \
    ParticularTransitionEducationGroupVersionFactory, StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory

COL_TEACHERS_LETTER = 'L'
COL_PROGRAMS_LETTER = 'Z'
PARENT_PARTIAL_ACRONYM = 'LDROI'
PARENT_ACRONYM = 'LBIR'
PARENT_TITLE = 'TITLE 1'
ROOT_ACRONYM = 'DRTI'
VERSION_ACRONYM = 'CRIM'


class TestLearningUnitXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2017)
        cls.learning_container_luy1 = LearningContainerYearFactory(academic_year=cls.academic_year)
        cls.learning_unit_yr_1 = LearningUnitYearFactory(academic_year=cls.academic_year,
                                                         learning_container_year=cls.learning_container_luy1,
                                                         credits=50)
        cls.learning_unit_yr_1_element = ElementFactory(learning_unit_year=cls.learning_unit_yr_1)
        cls.learning_unit_yr_2 = LearningUnitYearFactory()

        cls.proposal_creation_1 = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        cls.proposal_creation_2 = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        direct_parent_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)

        cls.an_education_group_parent = EducationGroupYearFactory(academic_year=cls.academic_year,
                                                                  education_group_type=direct_parent_type,
                                                                  acronym=ROOT_ACRONYM)
        cls.a_group_year_parent = GroupYearFactory(academic_year=cls.academic_year, acronym=ROOT_ACRONYM)
        cls.a_group_year_parent_element = ElementFactory(group_year=cls.a_group_year_parent)
        StandardEducationGroupVersionFactory(offer=cls.an_education_group_parent, root_group=cls.a_group_year_parent)

        cls.group_element_child = GroupElementYearFactory(
            parent_element=cls.a_group_year_parent_element,
            child_element=cls.learning_unit_yr_1_element
        )
        # Particular OF
        cls.create_version(direct_parent_type)
        #
        cls.an_education_group = EducationGroupYearFactory(academic_year=cls.academic_year,
                                                           acronym=PARENT_ACRONYM,
                                                           title=PARENT_TITLE,
                                                           partial_acronym=PARENT_PARTIAL_ACRONYM)

        cls.group_element_child2 = GroupElementYearFactory(
            parent=cls.an_education_group,
            child_branch=cls.group_element_child.parent,
        )
        cls.old_academic_year = AcademicYearFactory(year=datetime.date.today().year - 2)
        cls.current_academic_year = AcademicYearFactory(year=datetime.date.today().year)
        generatorContainer = GenerateContainer(cls.old_academic_year, cls.current_academic_year)
        cls.learning_unit_year_with_entities = generatorContainer.generated_container_years[0].learning_unit_year_full
        entities = [
            EntityVersionFactory(
                start_date=datetime.datetime(1900, 1, 1),
                end_date=None,
                entity_type=entity_type.FACULTY,
                entity__organization__type=organization_type.MAIN
            ) for _ in range(4)
        ]
        cls.learning_unit_year_with_entities.entity_requirement = entities[0]
        cls.learning_unit_year_with_entities.entity_allocation = entities[1]
        cls.proposal_creation_3 = ProposalLearningUnitFactory(
            learning_unit_year=cls.learning_unit_year_with_entities,
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        cls.learning_container_luy = LearningContainerYearFactory(academic_year=cls.academic_year)
        cls.luy_with_attribution = LearningUnitYearFactory(academic_year=cls.academic_year,
                                                           learning_container_year=cls.learning_container_luy,
                                                           periodicity=learning_unit_year_periodicity.ANNUAL,
                                                           status=True,
                                                           language=None,
                                                           )
        cls.luy_with_attribution.entity_requirement = entities[0]
        cls.luy_with_attribution.entity_allocation = entities[1]

        cls.component_lecturing = LearningComponentYearFactory(
            learning_unit_year=cls.luy_with_attribution,
            type=learning_component_year_type.LECTURING,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        cls.component_practical = LearningComponentYearFactory(
            learning_unit_year=cls.luy_with_attribution,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        a_person_tutor_1 = PersonFactory(last_name='Dupuis', first_name='Tom', email="dupuis@gmail.com")
        cls.a_tutor_1 = TutorFactory(person=a_person_tutor_1)

        cls.an_attribution_1 = AttributionNewFactory(
            tutor=cls.a_tutor_1,
            start_year=2017,
            function=COORDINATOR
        )
        cls.attribution_charge_new_lecturing_1 = AttributionChargeNewFactory(
            learning_component_year=cls.component_lecturing,
            attribution=cls.an_attribution_1,
            allocation_charge=15.0)
        cls.attribution_charge_new_practical_1 = AttributionChargeNewFactory(
            learning_component_year=cls.component_practical,
            attribution=cls.an_attribution_1,
            allocation_charge=5.0)

        cls.a_tutor_2 = TutorFactory(person=PersonFactory(last_name='Maréchal', first_name='Didier'))

        cls.an_attribution_2 = AttributionNewFactory(
            tutor=cls.a_tutor_2,
            start_year=2017
        )
        cls.attribution_charge_new_lecturing_2 = AttributionChargeNewFactory(
            learning_component_year=cls.component_lecturing,
            attribution=cls.an_attribution_2,
            allocation_charge=15.0)
        cls.attribution_charge_new_practical_2 = AttributionChargeNewFactory(
            learning_component_year=cls.component_practical,
            attribution=cls.an_attribution_2,
            allocation_charge=5.0)
        cls.entity_requirement = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__requirement_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        cls.entity_allocation = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__allocation_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

    @classmethod
    def create_version(cls, direct_parent_type):
        cls.learning_unit_yr_version = LearningUnitYearFactory(academic_year=cls.academic_year,
                                                               learning_container_year=LearningContainerYearFactory(academic_year=cls.academic_year),
                                                               credits=50)
        cls.learning_unit_yr_version_element = ElementFactory(learning_unit_year=cls.learning_unit_yr_version)
        cls.an_education_group_parent_for_particular_version = EducationGroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type=direct_parent_type,
            acronym=VERSION_ACRONYM)
        cls.a_group_year_parent_for_particular_version = GroupYearFactory(academic_year=cls.academic_year,
                                                                          acronym=VERSION_ACRONYM)
        cls.a_group_year_parent_element_for_particular_version = ElementFactory(
            group_year=cls.a_group_year_parent_for_particular_version)
        cls.particular_education_group_version = ParticularTransitionEducationGroupVersionFactory(
            offer=cls.an_education_group_parent_for_particular_version,
            root_group=cls.a_group_year_parent_for_particular_version)
        GroupElementYearFactory(
            parent_element=cls.a_group_year_parent_element_for_particular_version,
            child_element=cls.learning_unit_yr_version_element
        )

    def test_get_wrapped_cells_with_teachers_and_programs(self):
        styles = _get_wrapped_cells([self.learning_unit_yr_1, self.learning_unit_yr_2],
                                    COL_TEACHERS_LETTER,
                                    COL_PROGRAMS_LETTER)
        self.assertCountEqual(styles, ['{}2'.format(COL_TEACHERS_LETTER),
                                       '{}2'.format(COL_PROGRAMS_LETTER),
                                       '{}3'.format(COL_TEACHERS_LETTER),
                                       '{}3'.format(COL_PROGRAMS_LETTER)])

    def test_get_wrapped_cells_with_teachers(self):
        styles = _get_wrapped_cells([self.learning_unit_yr_1, self.learning_unit_yr_2], COL_TEACHERS_LETTER, None)
        self.assertCountEqual(styles, ['{}2'.format(COL_TEACHERS_LETTER),
                                       '{}3'.format(COL_TEACHERS_LETTER)])

    def test_get_wrapped_cells_with_programs(self):
        styles = _get_wrapped_cells([self.learning_unit_yr_1, self.learning_unit_yr_2], None, COL_PROGRAMS_LETTER)
        self.assertCountEqual(styles, ['{}2'.format(COL_PROGRAMS_LETTER),
                                       '{}3'.format(COL_PROGRAMS_LETTER)])

    def test_get_col_letter(self):
        title_searched = 'title 2'
        titles = ['title 1', title_searched, 'title 3']
        self.assertEqual(_get_col_letter(titles, title_searched), 'B')
        self.assertIsNone(_get_col_letter(titles, 'whatever'))

    def test_get_colored_rows(self):
        self.assertEqual(_get_font_rows([self.learning_unit_yr_1,
                                         self.learning_unit_yr_2,
                                         self.proposal_creation_1.learning_unit_year,
                                         self.proposal_creation_2.learning_unit_year]),
                         {PROPOSAL_LINE_STYLES.get(self.proposal_creation_1.type): [3, 4]})

    def test_get_attributions_line(self):
        a_person = PersonFactory(last_name="Smith", first_name='Aaron')
        attribution_dict = {
            'LECTURING': 10,
            'substitute': None,
            'duration': 3,
            'PRACTICAL_EXERCISES': 15,
            'person': a_person,
            'function': 'CO_HOLDER',
            'start_year': self.academic_year
        }
        self.assertEqual(
            _get_attribution_line(attribution_dict),
            "{} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} ".format(
                'SMITH, Aaron', _('Function'),
                _('Co-holder'), _('Substitute'),
                '', _('Beg. of attribution'),
                self.academic_year, _('Attribution duration'),
                3, _('Attrib. vol1'),
                10, _('Attrib. vol2'),
                15,
            )
        )

    def test_get_significant_volume(self):
        self.assertEqual(get_significant_volume(10), 10)
        self.assertEqual(get_significant_volume(None), '')
        self.assertEqual(get_significant_volume(0), '')

    def test_prepare_legend_ws_data(self):
        expected = {
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
                DEFAULT_LEGEND_FILLS
        }
        self.assertEqual(prepare_proposal_legend_ws_data(), expected)

    def test_add_training_data(self):
        luy_1 = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_1.pk).annotate(
            closest_trainings=RawSQL(SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS, ())
        ).get()
        formations = _add_training_data(luy_1)
        expected = "{} ({}) - {} - {}".format(
            self.a_group_year_parent.partial_acronym,
            "{0:.2f}".format(luy_1.credits),
            self.a_group_year_parent.acronym,
            self.a_group_year_parent.title_fr
        )
        self.assertEqual(formations, expected)

    def test_get_data_part1(self):
        luy = self.proposal_creation_3.learning_unit_year
        data = _get_data_part1(luy)
        self.assertEqual(data[0], luy.acronym)
        self.assertEqual(data[1], luy.academic_year.name)
        self.assertEqual(data[2], luy.complete_title)
        self.assertEqual(data[6], _(self.proposal_creation_1.type.title()))
        self.assertEqual(data[7], _(self.proposal_creation_1.state.title()))

    def test_get_parameters_configurable_list(self):
        user_name = 'Ducon'
        an_user = UserFactory(username=user_name)
        titles = ['title1', 'title2']
        learning_units = [self.learning_unit_yr_1, self.learning_unit_yr_2]
        param = _get_parameters_configurable_list(learning_units, titles, an_user)
        self.assertEqual(param.get(xls_build.DESCRIPTION), XLS_DESCRIPTION)
        self.assertEqual(param.get(xls_build.USER), user_name)
        self.assertEqual(param.get(xls_build.HEADER_TITLES), titles)
        self.assertEqual(param.get(xls_build.ALIGN_CELLS), {WRAP_TEXT_ALIGNMENT: []})
        self.assertEqual(param.get(xls_build.FONT_ROWS), {})

        titles.append(HEADER_PROGRAMS)

        param = _get_parameters_configurable_list(learning_units, titles, an_user)
        self.assertEqual(param.get(xls_build.ALIGN_CELLS), {WRAP_TEXT_ALIGNMENT: ['C2', 'C3']})

    def test_get_data_part2(self):
        learning_container_luy = LearningContainerYearFactory(academic_year=self.academic_year)
        luy = LearningUnitYearFactory(academic_year=self.academic_year,
                                      learning_container_year=learning_container_luy,
                                      periodicity=learning_unit_year_periodicity.ANNUAL,
                                      status=True,
                                      language=None,
                                      )

        component_lecturing = LearningComponentYearFactory(
            learning_unit_year=luy,
            type=learning_component_year_type.LECTURING,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        component_practical = LearningComponentYearFactory(
            learning_unit_year=luy,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        a_tutor = TutorFactory()

        an_attribution = AttributionNewFactory(
            tutor=a_tutor,
            start_year=2017
        )

        attribution_charge_new_lecturing = AttributionChargeNewFactory(learning_component_year=component_lecturing,
                                                                       attribution=an_attribution,
                                                                       allocation_charge=15.0)
        attribution_charge_new_practical = AttributionChargeNewFactory(learning_component_year=component_practical,
                                                                       attribution=an_attribution,
                                                                       allocation_charge=5.0)

        # Simulate annotate
        luy = annotate_qs(LearningUnitYear.objects.filter(pk=luy.pk)).first()
        luy.entity_requirement = EntityVersionFactory()

        luy.attribution_charge_news = attribution_charge_new.find_attribution_charge_new_by_learning_unit_year_as_dict(
            luy)

        expected_common = [
            str(_(luy.periodicity.title())),
            str(_('yes')) if luy.status else str(_('no')),
            component_lecturing.hourly_volume_total_annual,
            component_lecturing.hourly_volume_partial_q1,
            component_lecturing.hourly_volume_partial_q2,
            component_lecturing.planned_classes,
            component_practical.hourly_volume_total_annual,
            component_practical.hourly_volume_partial_q1,
            component_practical.hourly_volume_partial_q2,
            component_practical.planned_classes,
            luy.get_quadrimester_display() or '',
            luy.get_session_display() or '',
            "",
        ]
        self.assertEqual(_get_data_part2(luy, False), expected_common)
        self.assertEqual(
            _get_data_part2(luy, True),
            expected_attribution_data(
                attribution_charge_new_lecturing, attribution_charge_new_practical,
                expected_common,
                luy
            )
        )

    def test_learning_unit_titles_part1(self):
        self.assertEqual(
            learning_unit_titles_part1(),
            [
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
        )

    def test_prepare_xls_content(self):
        qs = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_1.pk).annotate(
            entity_requirement=Subquery(self.entity_requirement),
            entity_allocation=Subquery(self.entity_allocation),
        )
        result = prepare_xls_content(qs, with_grp=True, with_attributions=True)
        self.assertEqual(len(result), 1)

        luy = annotate_qs(qs).get()
        self.assertListEqual(
            result[0],
            self._get_luy_expected_data(luy)
        )

    def _get_luy_expected_data(self, luy):
        return [
            luy.acronym,
            luy.academic_year.__str__(),
            luy.complete_title,
            luy.get_container_type_display(),
            luy.get_subtype_display(),
            luy.entity_requirement,
            '',  # Proposal
            '',  # Proposal state
            luy.credits,
            luy.entity_allocation,
            luy.complete_title_english,
            '',
            luy.get_periodicity_display(),
            yesno(luy.status),
            get_significant_volume(luy.pm_vol_tot or 0),
            get_significant_volume(luy.pm_vol_q1 or 0),
            get_significant_volume(luy.pm_vol_q2 or 0),
            luy.pm_classes or 0,
            get_significant_volume(luy.pp_vol_tot or 0),
            get_significant_volume(luy.pp_vol_q1 or 0),
            get_significant_volume(luy.pp_vol_q2 or 0),
            luy.pp_classes or 0,
            luy.get_quadrimester_display() or '',
            luy.get_session_display() or '',
            luy.language or "",
            "{} ({}) - {} - {}".format(self.a_group_year_parent.partial_acronym,
                                         "{0:.2f}".format(luy.credits),
                                         self.a_group_year_parent.acronym,
                                         self.a_group_year_parent.title_fr)
        ]

    def test_get_attribution_detail(self):
        a_person = PersonFactory(last_name="Smith", first_name='Aaron', email='smith@google.com')
        attribution_dict = {
            'LECTURING': 10,
            'substitute': None,
            'duration': 3,
            'PRACTICAL_EXERCISES': 15,
            'person': a_person,
            'function': 'CO_HOLDER',
            'start_year': self.academic_year
        }
        self.assertCountEqual(
            _get_attribution_detail(attribution_dict),
            ['Smith Aaron',
             'smith@google.com',
             _('Co-holder'),
             '',
             self.academic_year,
             3,
             10,
             15]
        )

    def test_prepare_xls_content_with_attributions(self):
        qs = LearningUnitYear.objects.filter(pk=self.luy_with_attribution.pk).annotate(
            entity_requirement=Subquery(self.entity_requirement),
            entity_allocation=Subquery(self.entity_allocation),
        )
        result = prepare_xls_content_with_attributions(qs, 31)
        self.assertEqual(len(result.get('data')), 2)
        self.assertCountEqual(result.get('cells_with_top_border'), ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
                                                                    'I2', 'J2', 'K2', 'L2', 'M2', 'N2', 'O2', 'P2',
                                                                    'Q2', 'R2', 'S2', 'T2', 'U2', 'V2', 'W2', 'X2',
                                                                    'Y2', 'Z2', 'AA2', 'AB2', 'AC2', 'AD2', 'AE2']
                              )
        self.assertCountEqual(result.get('cells_with_white_font'), ['A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
                                                                    'I3', 'J3', 'K3', 'L3', 'M3', 'N3', 'O3', 'P3',
                                                                    'Q3', 'R3', 'S3', 'T3', 'U3', 'V3', 'W3', 'X3']
                              )
        first_attribution = result.get('data')[0]

        self.assertEqual(first_attribution[24], 'Dupuis Tom')
        self.assertEqual(first_attribution[25], 'dupuis@gmail.com')
        self.assertEqual(first_attribution[26], _("Coordinator"))
        self.assertEqual(first_attribution[27], "")
        self.assertEqual(first_attribution[28], 2017)
        self.assertEqual(first_attribution[29], '')
        self.assertEqual(first_attribution[30], 15)
        self.assertEqual(first_attribution[31], 5)

    def test_add_training_data_for_version(self):
        luy = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_version.pk).annotate(
            closest_trainings=RawSQL(SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS, ())
        ).get()

        formations = _add_training_data(luy)
        expected = "{} ({}) - {} - {}".format(
            self.a_group_year_parent_for_particular_version.partial_acronym,
            "{0:.2f}".format(luy.credits),
            "{}[{}-Transition]".format(self.a_group_year_parent_for_particular_version.acronym,
                                       self.particular_education_group_version.version_name),
            self.a_group_year_parent_for_particular_version.title_fr
        )
        self.assertEqual(formations, expected)


def expected_attribution_data(attribution_charge_new_lecturing, attribution_charge_new_practical, expected, luy):
    expected_attribution = None
    for k, v in luy.attribution_charge_news.items():
        expected_attribution = v
    expected_attribution = "{} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} ".format(
        expected_attribution.get('person'),
        _('Function'),
        Functions[expected_attribution['function']].value,
        _('Substitute'),
        '',
        _('Beg. of attribution'),
        expected_attribution.get('start_year'),
        _('Attribution duration'),
        expected_attribution.get('duration'),
        _('Attrib. vol1'),
        attribution_charge_new_lecturing.allocation_charge,
        _('Attrib. vol2'),
        attribution_charge_new_practical.allocation_charge, )
    ex = [expected_attribution]
    ex.extend(expected)
    return ex
