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
from django.utils.translation import ugettext_lazy as _

from attribution.business import attribution_charge_new
from attribution.models.enums.function import COORDINATOR
from attribution.models.enums.function import Functions
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business.learning_unit_xls import DEFAULT_LEGEND_STYLES, SPACES, PROPOSAL_LINE_STYLES, \
    _get_significant_volume, _prepare_legend_ws_data, _get_wrapped_cells, \
    _get_colored_rows, _get_attribution_line, _add_training_data, \
    _get_data_part1, _get_parameters_configurable_list, WRAP_TEXT_STYLE, HEADER_PROGRAMS, XLS_DESCRIPTION, \
    _get_data_part2, annotate_qs, learning_unit_titles_part1, prepare_xls_content, _get_attribution_detail, \
    prepare_xls_content_with_attributions
from base.business.learning_unit_xls import _get_col_letter
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
from osis_common.document import xls_build

COL_TEACHERS_LETTER = 'L'
COL_PROGRAMS_LETTER = 'Z'
PARENT_PARTIAL_ACRONYM = 'LDROI'
PARENT_ACRONYM = 'LBIR'
PARENT_TITLE = 'TITLE 1'
ROOT_ACRONYM = 'DRTI'


class TestLearningUnitXls(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(year=2017)
        self.learning_container_luy1 = LearningContainerYearFactory(academic_year=self.academic_year)
        self.learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                          learning_container_year=self.learning_container_luy1,
                                                          credits=50)
        self.learning_unit_yr_2 = LearningUnitYearFactory()

        self.proposal_creation_1 = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        self.proposal_creation_2 = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        direct_parent_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)

        self.an_education_group_parent = EducationGroupYearFactory(academic_year=self.academic_year,
                                                                   education_group_type=direct_parent_type,
                                                                   acronym=ROOT_ACRONYM)
        self.group_element_child = GroupElementYearFactory(
            parent=self.an_education_group_parent,
            child_branch=None,
            child_leaf=self.learning_unit_yr_1
        )
        self.an_education_group = EducationGroupYearFactory(academic_year=self.academic_year,
                                                            acronym=PARENT_ACRONYM,
                                                            title=PARENT_TITLE,
                                                            partial_acronym=PARENT_PARTIAL_ACRONYM)

        self.group_element_child2 = GroupElementYearFactory(
            parent=self.an_education_group,
            child_branch=self.group_element_child.parent,
        )
        self.old_academic_year = AcademicYearFactory(year=datetime.date.today().year - 2)
        self.current_academic_year = AcademicYearFactory(year=datetime.date.today().year)
        generatorContainer = GenerateContainer(self.old_academic_year, self.current_academic_year)
        self.learning_unit_year_with_entities = generatorContainer.generated_container_years[0].learning_unit_year_full
        entities = [
            EntityVersionFactory(
                start_date=datetime.datetime(1900, 1, 1),
                end_date=None,
                entity_type=entity_type.FACULTY,
                entity__organization__type=organization_type.MAIN
            ) for _ in range(4)
        ]
        self.learning_unit_year_with_entities.entity_requirement = entities[0]
        self.learning_unit_year_with_entities.entity_allocation = entities[1]
        self.proposal_creation_3 = ProposalLearningUnitFactory(
            learning_unit_year=self.learning_unit_year_with_entities,
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
        )
        self.learning_container_luy = LearningContainerYearFactory(academic_year=self.academic_year)
        self.luy_with_attribution = LearningUnitYearFactory(academic_year=self.academic_year,
                                                            learning_container_year=self.learning_container_luy,
                                                            periodicity=learning_unit_year_periodicity.ANNUAL,
                                                            status=True,
                                                            language=None,
                                                            )
        self.luy_with_attribution.entity_requirement = entities[0]
        self.luy_with_attribution.entity_allocation = entities[1]

        self.component_lecturing = LearningComponentYearFactory(
            learning_unit_year=self.luy_with_attribution,
            type=learning_component_year_type.LECTURING,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        self.component_practical = LearningComponentYearFactory(
            learning_unit_year=self.luy_with_attribution,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        a_person_tutor_1 = PersonFactory(last_name='Dupuis', first_name='Tom')
        self.a_tutor_1 = TutorFactory(person=a_person_tutor_1)

        self.an_attribution_1 = AttributionNewFactory(
            tutor=self.a_tutor_1,
            start_year=2017,
            function=COORDINATOR
        )
        self.attribution_charge_new_lecturing_1 = AttributionChargeNewFactory(
            learning_component_year=self.component_lecturing,
            attribution=self.an_attribution_1,
            allocation_charge=15.0)
        self.attribution_charge_new_practical_1 = AttributionChargeNewFactory(
            learning_component_year=self.component_practical,
            attribution=self.an_attribution_1,
            allocation_charge=5.0)

        self.a_tutor_2 = TutorFactory(person=PersonFactory(last_name='Maréchal', first_name='Didier'))

        self.an_attribution_2 = AttributionNewFactory(
            tutor=self.a_tutor_2,
            start_year=2017
        )
        self.attribution_charge_new_lecturing_2 = AttributionChargeNewFactory(
            learning_component_year=self.component_lecturing,
            attribution=self.an_attribution_2,
            allocation_charge=15.0)
        self.attribution_charge_new_practical_2 = AttributionChargeNewFactory(
            learning_component_year=self.component_practical,
            attribution=self.an_attribution_2,
            allocation_charge=5.0)
        self.entity_requirement = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__requirement_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        self.entity_allocation = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__allocation_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

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
        self.assertEqual(_get_colored_rows([self.learning_unit_yr_1,
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
        self.assertEqual(_get_significant_volume(10), 10)
        self.assertEqual(_get_significant_volume(None), '')
        self.assertEqual(_get_significant_volume(0), '')

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
                DEFAULT_LEGEND_STYLES
        }
        self.assertEqual(_prepare_legend_ws_data(), expected)

    def test_add_training_data(self):
        luy_1 = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_1.pk).annotate(
            closest_trainings=RawSQL(SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS, ())
        ).get()
        formations = _add_training_data(luy_1)
        expected = "{} ({}) - {} - {}\n".format(self.an_education_group_parent.partial_acronym,
                                                "{0:.2f}".format(luy_1.credits),
                                                self.an_education_group_parent.acronym,
                                                self.an_education_group_parent.title)
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
        self.assertEqual(param.get(xls_build.STYLED_CELLS), {WRAP_TEXT_STYLE: []})
        self.assertEqual(param.get(xls_build.COLORED_ROWS), {})

        titles.append(HEADER_PROGRAMS)

        param = _get_parameters_configurable_list(learning_units, titles, an_user)
        self.assertEqual(param.get(xls_build.STYLED_CELLS), {WRAP_TEXT_STYLE: ['C2', 'C3']})

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
            _get_significant_volume(luy.pm_vol_tot or 0),
            _get_significant_volume(luy.pm_vol_q1 or 0),
            _get_significant_volume(luy.pm_vol_q2 or 0),
            luy.pm_classes or 0,
            _get_significant_volume(luy.pp_vol_tot or 0),
            _get_significant_volume(luy.pp_vol_q1 or 0),
            _get_significant_volume(luy.pp_vol_q2 or 0),
            luy.pp_classes or 0,
            luy.get_quadrimester_display() or '',
            luy.get_session_display() or '',
            luy.language or "",
            "{} ({}) - {} - {}\n".format(self.an_education_group_parent.partial_acronym,
                                         "{0:.2f}".format(luy.credits),
                                         self.an_education_group_parent.acronym,
                                         self.an_education_group_parent.title)
        ]

    def test_get_attribution_detail(self):
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
        self.assertCountEqual(
            _get_attribution_detail(attribution_dict),
            ['Smith Aaron',
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
        self.assertEqual(first_attribution[25], _("Coordinator"))
        self.assertEqual(first_attribution[26], "")
        self.assertEqual(first_attribution[27], 2017)
        self.assertEqual(first_attribution[28], '')
        self.assertEqual(first_attribution[29], 15)
        self.assertEqual(first_attribution[30], 5)


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
