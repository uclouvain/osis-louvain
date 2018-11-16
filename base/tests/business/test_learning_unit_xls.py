##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from attribution.models.enums.function import Functions
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.person import PersonFactory
from base.business.learning_unit_xls import DEFAULT_LEGEND_STYLES, SPACES, PROPOSAL_LINE_STYLES, _update_volumes_data, \
    _get_significant_volume, VOLUMES_INITIALIZED, _prepare_legend_ws_data, _get_wrapped_cells, \
    _get_colored_rows, _get_attribution_line, _get_col_letter, _get_trainings_by_educ_group_year, _add_training_data, \
    _get_data_part1, _get_parameters_configurable_list, WRAP_TEXT_STYLE, HEADER_PROGRAMS, XLS_DESCRIPTION, \
    _get_absolute_credits, _get_volumes, _get_data_part2
from base.models.enums import proposal_type, proposal_state
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.models.enums import learning_component_year_type
from osis_common.document import xls_build
from base.models.enums import education_group_categories
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_type, organization_type
from base.tests.factories.user import UserFactory
from base.models.enums import learning_unit_year_periodicity
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.business import attribution_charge_new
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory

COL_TEACHERS_LETTER = 'L'
COL_PROGRAMS_LETTER = 'Z'
PARENT_PARTIAL_ACRONYM = 'LDROI'
PARENT_ACRONYM = 'LBIR'
PARENT_TITLE = 'TITLE 1'
ROOT_ACRONYM = 'DRTI'


class TestLearningUnitXls(TestCase):
    def setUp(self):
        self.current_academic_year = AcademicYearFactory(year=2017)
        self.learning_container_luy1 = LearningContainerYearFactory(academic_year=self.current_academic_year)
        self.learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
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

        self.an_education_group_parent = EducationGroupYearFactory(academic_year=self.current_academic_year,
                                                                   education_group_type=direct_parent_type,
                                                                   acronym=ROOT_ACRONYM)
        self.group_element_child = GroupElementYearFactory(
            parent=self.an_education_group_parent,
            child_branch=None,
            child_leaf=self.learning_unit_yr_1
        )
        self.an_education_group = EducationGroupYearFactory(academic_year=self.current_academic_year,
                                                            acronym=PARENT_ACRONYM,
                                                            title=PARENT_TITLE,
                                                            partial_acronym=PARENT_PARTIAL_ACRONYM)

        self.group_element_child2 = GroupElementYearFactory(
            parent=self.an_education_group,
            child_branch=self.group_element_child.parent,
        )
        generatorContainer = GenerateContainer(datetime.date.today().year - 2, datetime.date.today().year)
        self.learning_unit_year_with_entities = generatorContainer.generated_container_years[0].learning_unit_year_full
        entities = [
            EntityVersionFactory(
                start_date=datetime.datetime(1900, 1, 1),
                end_date=None,
                entity_type=entity_type.FACULTY,
                entity__organization__type=organization_type.MAIN
            ) for _ in range(4)
        ]
        self.learning_unit_year_with_entities.entities = {'REQUIREMENT_ENTITY': entities[0],
                                                          'ALLOCATION_ENTITY': entities[1]}
        self.proposal_creation_3 = ProposalLearningUnitFactory(
            learning_unit_year=self.learning_unit_year_with_entities,
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.CREATION.name,
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
            'start_year': 2017
        }
        self.assertEqual(
            _get_attribution_line(attribution_dict),
            "{} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} - {} : {} ".format(
                'SMITH, Aaron', _('Function'),
                _('Co-holder'), _('Substitute'),
                '', _('Beg. of attribution'),
                2017, _('Attribution duration'),
                3, _('Attrib. vol1'),
                10, _('Attrib. vol2'),
                15,
            )
        )

    def test_get_significant_volume(self):
        self.assertEqual(_get_significant_volume(10), 10)
        self.assertEqual(_get_significant_volume(None), '')
        self.assertEqual(_get_significant_volume(0), '')

    def test_update_volumes_data(self):
        volumes = {
            learning_component_year_type.LECTURING: VOLUMES_INITIALIZED,
            learning_component_year_type.PRACTICAL_EXERCISES: VOLUMES_INITIALIZED
        }
        lecturing_data = {'PLANNED_CLASSES': 1, 'VOLUME_Q1': 10, 'VOLUME_TOTAL': 50, 'VOLUME_Q2': 40}
        compo = {
            'learning_component_year': LearningComponentYearFactory(
                learning_container_year=self.learning_container_luy1,
                type=learning_component_year_type.LECTURING),
            'volumes': lecturing_data
        }
        volumes_updated = _update_volumes_data(compo, volumes)
        self.assertCountEqual(volumes_updated.get(learning_component_year_type.LECTURING),
                              lecturing_data)
        self.assertCountEqual(volumes_updated.get(learning_component_year_type.PRACTICAL_EXERCISES),
                              VOLUMES_INITIALIZED)

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

    def test_get_formations_by_educ_group_year(self):
        formations = _get_trainings_by_educ_group_year(self.learning_unit_yr_1)
        self.assertCountEqual(formations.get(self.an_education_group_parent.id),
                              [self.an_education_group])

    def test_add_training_data(self):
        formations = _add_training_data(self.learning_unit_yr_1)

        expected = "{} {} {}".format(
            self.an_education_group_parent.partial_acronym,
            "({})".format(
                '{0:.2f}'.format(self.learning_unit_yr_1.credits)
            ),
            "{} - {}".format(PARENT_ACRONYM, PARENT_TITLE)
        )

        self.assertEqual(formations, expected)

    def test_get_data_part1(self):
        luy = self.proposal_creation_3.learning_unit_year
        data = _get_data_part1(luy)
        self.assertEqual(data[0], luy.acronym)
        self.assertEqual(data[1], luy.academic_year.name)
        self.assertEqual(data[2], luy.complete_title)
        self.assertEqual(data[6], _(self.proposal_creation_1.type))
        self.assertEqual(data[7], _(self.proposal_creation_1.state))

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

    def test_get_absolute_credits(self):
        credits_luy = 15
        luy = LearningUnitYearFactory(credits=credits_luy)
        GroupElementYearFactory(
            child_branch=None,
            child_leaf=luy
        )
        self.assertEqual(_get_absolute_credits(luy), credits_luy)

    def test_get_absolute_credits_empty(self):
        luy = LearningUnitYearFactory(credits=None)
        GroupElementYearFactory(
            child_branch=None,
            child_leaf=luy
        )
        self.assertEqual(_get_absolute_credits(luy), '')

    def test_get_volumes(self):
        learning_container_luy = LearningContainerYearFactory(academic_year=self.current_academic_year)
        luy = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                      learning_container_year=learning_container_luy)

        LearningComponentYearFactory(
            learning_container_year=learning_container_luy,
            type=learning_component_year_type.LECTURING,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        LearningComponentYearFactory(
            learning_container_year=learning_container_luy,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            hourly_volume_total_annual=20,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10,
            planned_classes=1
        )
        volumes = _get_volumes(luy)
        self.assertEqual(volumes.get('LECTURING'),
                         {'VOLUME_TOTAL': 15, 'PLANNED_CLASSES': 1, 'VOLUME_Q1': 10, 'VOLUME_Q2': 5})
        self.assertEqual(volumes.get('PRACTICAL_EXERCISES'),
                         {'VOLUME_TOTAL': 20, 'PLANNED_CLASSES': 1, 'VOLUME_Q1': 10, 'VOLUME_Q2': 10})

    def test_get_data_part2(self):
        learning_container_luy = LearningContainerYearFactory(academic_year=self.current_academic_year)
        luy = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                      learning_container_year=learning_container_luy,
                                      periodicity=learning_unit_year_periodicity.ANNUAL,
                                      status=True,
                                      language=None,
                                      )

        component_lecturing = LearningComponentYearFactory(
            learning_container_year=learning_container_luy,
            type=learning_component_year_type.LECTURING,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        component_practical = LearningComponentYearFactory(
            learning_container_year=learning_container_luy,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            hourly_volume_total_annual=15,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=5,
            planned_classes=1
        )
        LearningUnitComponentFactory(learning_unit_year=luy, learning_component_year=component_lecturing)
        LearningUnitComponentFactory(learning_unit_year=luy, learning_component_year=component_practical)
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

        luy.attribution_charge_news = attribution_charge_new.find_attribution_charge_new_by_learning_unit_year_as_dict(
            luy)
        expected_common = [
            xls_build.translate(luy.periodicity),
            xls_build.translate(luy.status),
            component_lecturing.hourly_volume_total_annual,
            component_lecturing.hourly_volume_partial_q1,
            component_lecturing.hourly_volume_partial_q2,
            component_lecturing.planned_classes,
            component_practical.hourly_volume_total_annual,
            component_practical.hourly_volume_partial_q1,
            component_practical.hourly_volume_partial_q2,
            component_practical.planned_classes,
            xls_build.translate(luy.quadrimester),
            xls_build.translate(luy.session),
            "",
            ''
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
