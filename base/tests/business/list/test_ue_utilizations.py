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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from collections import defaultdict

from django.db.models.expressions import Subquery, OuterRef
from django.template.defaultfilters import yesno
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business.learning_unit_xls import WRAP_TEXT_ALIGNMENT, annotate_qs, PROPOSAL_LINE_STYLES, \
    get_significant_volume
from base.business.list.ue_utilizations import _get_parameters, CELLS_WITH_BORDER_TOP, \
    WHITE_FONT, BOLD_FONT, _prepare_xls_content, _prepare_titles, CELLS_TO_COLOR, XLS_DESCRIPTION, _check_cell_to_color
from base.models.entity_version import EntityVersion
from base.models.enums import education_group_categories
from base.models.enums import learning_component_year_type
from base.models.enums import proposal_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.tutor import Tutor
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory
from education_group.tests.factories.group_year import GroupYearFactory
from osis_common.document import xls_build
from program_management.tests.factories.education_group_version import \
    StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory

TRAINING_TITLE_COLUMN = 28
TRAINING_CODE_COLUMN = 27
GATHERING_COLUMN = 26
ROOT_ACRONYM = 'DRTI'
VERSION_ACRONYM = 'CRIM'


class TestUeUtilization(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.learning_container_luy1 = LearningContainerYearFactory(academic_year=cls.academic_year)
        cls.learning_unit_yr_1 = LearningUnitYearFactory(academic_year=cls.academic_year,
                                                         learning_container_year=cls.learning_container_luy1,
                                                         credits=10)
        cls.learning_unit_yr_1_element = ElementFactory(learning_unit_year=cls.learning_unit_yr_1)
        cls.learning_unit_yr_2 = LearningUnitYearFactory()
        cls.learning_unit_yr_2_element = ElementFactory(learning_unit_year=cls.learning_unit_yr_2)

        direct_parent_type = EducationGroupTypeFactory(name='Bachelor', category=education_group_categories.TRAINING)

        cls.an_education_group_parent = EducationGroupYearFactory(academic_year=cls.academic_year,
                                                                  education_group_type=direct_parent_type,
                                                                  acronym=ROOT_ACRONYM)
        cls.a_group_year_parent = GroupYearFactory(academic_year=cls.academic_year,
                                                   acronym=ROOT_ACRONYM)
        cls.a_group_year_parent_element = ElementFactory(group_year=cls.a_group_year_parent)
        cls.standard_version = StandardEducationGroupVersionFactory(
            offer=cls.an_education_group_parent, root_group=cls.a_group_year_parent
        )

        cls.group_element_child = GroupElementYearFactory(
            parent_element=cls.a_group_year_parent_element,
            child_element=cls.learning_unit_yr_1_element,
            relative_credits=cls.learning_unit_yr_1.credits,
        )
        cls.group_element_child_1 = GroupElementYearFactory(
            parent_element=cls.a_group_year_parent_element,
            child_element=cls.learning_unit_yr_2_element,
            relative_credits=cls.learning_unit_yr_2.credits,
        )
        cls.an_education_group_parent_2 = EducationGroupYearFactory(academic_year=cls.academic_year,
                                                                    education_group_type=direct_parent_type,
                                                                    acronym='PRMR')
        cls.a_group_year_parent_2 = GroupYearFactory(academic_year=cls.academic_year, acronym='PRMR')
        cls.a_group_year_parent_element_2 = ElementFactory(group_year=cls.a_group_year_parent_2)
        cls.standard_version_2 = StandardEducationGroupVersionFactory(
            offer=cls.an_education_group_parent_2, root_group=cls.a_group_year_parent_2
        )
        cls.group_element_child_2 = GroupElementYearFactory(
            parent_element=cls.a_group_year_parent_element_2,
            child_element=cls.learning_unit_yr_2_element,
            relative_credits=cls.learning_unit_yr_2.credits,
        )
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
        cls.learning_unit_yr_with_proposal = LearningUnitYearFactory(academic_year=cls.academic_year)
        cls.proposal = ProposalLearningUnitFactory(
            learning_unit_year=cls.learning_unit_yr_with_proposal,
            type=proposal_type.ProposalType.MODIFICATION.name,
        )
        
        cls.a_tutor = _create_tutor_and_attributions(cls.learning_unit_yr_1)

    def test_headers(self):
        self.assertListEqual(_prepare_titles(),
                             [
                                 str(_('Code')),
                                 str(_('Ac yr.')),
                                 str(_('Title')),
                                 str(_('Type')),
                                 str(_('Subtype')),
                                 str(_('Req. Entity')),
                                 str(_('Proposal type')),
                                 str(_('Proposal status')),
                                 str(_('Credits')),
                                 str(_('Alloc. Ent.')),
                                 str(_('Title in English')),
                                 str(_('List of teachers')),
                                 str(_('List of teachers (email)')),
                                 str(_('Periodicity')),
                                 str(_('Active')),
                                 "{} - {}".format(_('Lecturing vol.'), _('Annual')),
                                 "{} - {}".format(_('Lecturing vol.'), _('1st quadri')),
                                 "{} - {}".format(_('Lecturing vol.'), _('2nd quadri')),
                                 "{}".format(_('Lecturing planned classes')),
                                 "{} - {}".format(_('Practical vol.'), _('Annual')),
                                 "{} - {}".format(_('Practical vol.'), _('1st quadri')),
                                 "{} - {}".format(_('Practical vol.'), _('2nd quadri')),
                                 "{}".format(_('Practical planned classes')),
                                 str(_('Quadrimester')),
                                 str(_('Session derogation')),
                                 str(_('Language')),
                                 str(_('Gathering')), str(_('Training code')), str(_('Training title')),
                                 str(_('Training management entity')),

                             ]
                             )

    def test_get_parameters(self):
        an_user = UserFactory()
        titles = ['title1', 'title2']
        learning_units = [self.learning_unit_yr_1, self.learning_unit_yr_2]
        data = {CELLS_WITH_BORDER_TOP: [], CELLS_TO_COLOR: []}

        param = _get_parameters(data, learning_units, titles, an_user)
        self.assertEqual(param.get(xls_build.DESCRIPTION), XLS_DESCRIPTION)
        self.assertEqual(param.get(xls_build.USER), an_user.username)
        self.assertEqual(param.get(xls_build.HEADER_TITLES), titles)
        self.assertEqual(param.get(xls_build.ALIGN_CELLS), {WRAP_TEXT_ALIGNMENT: []})
        self.assertEqual(param.get(xls_build.FONT_ROWS), {BOLD_FONT: [0]})
        self.assertEqual(param.get(xls_build.BORDER_CELLS), {xls_build.BORDER_TOP: data.get(CELLS_WITH_BORDER_TOP)})
        self.assertEqual(param.get(xls_build.FONT_CELLS), [])

    def test_prepare_xls_content_ue_used_in_one_training(self):
        qs = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_1.pk).annotate(
            entity_requirement=Subquery(self.entity_requirement),
            entity_allocation=Subquery(self.entity_allocation),
        )
        result = _prepare_xls_content(qs)
        self.assertEqual(len(result.get("working_sheets_data")), 1)

        luy = annotate_qs(qs).get()
        self.assertListEqual(
            result.get("working_sheets_data")[0],
            self._get_luy_expected_data(luy, self.a_tutor)
        )

    def test_prepare_xls_content_ue_used_in_2_trainings(self):
        qs = LearningUnitYear.objects.filter(pk=self.learning_unit_yr_2.pk).annotate(
            entity_requirement=Subquery(self.entity_requirement),
            entity_allocation=Subquery(self.entity_allocation),
        )
        result = _prepare_xls_content(qs)
        self.assertEqual(len(result.get("working_sheets_data")), 2)
        first_training_occurence = result.get("working_sheets_data")[0]
        second_training_occurence = result.get("working_sheets_data")[1]

        res1 = "{} ({})".format(
            self.a_group_year_parent.partial_acronym,
            "{0:.2f}".format(self.group_element_child_1.relative_credits),
            )

        res2 = "{} ({})".format(
            self.a_group_year_parent_2.partial_acronym,
            "{0:.2f}".format(self.group_element_child_2.relative_credits),
            )
        results = [res1, res2]
        self.assertCountEqual(
            results,
            [
                first_training_occurence[GATHERING_COLUMN],
                second_training_occurence[GATHERING_COLUMN]
            ]
        )
        res1 = "{}".format(self.a_group_year_parent.acronym)

        res2 = "{}".format(self.a_group_year_parent_2.acronym)

        results = [res1, res2]
        self.assertCountEqual(
            results,
            [
                first_training_occurence[TRAINING_CODE_COLUMN],
                second_training_occurence[TRAINING_CODE_COLUMN]
            ]
        )
        res1 = "{}".format(self.a_group_year_parent.title_fr + ' [{}]'.format(self.standard_version.title_fr))
        res2 = "{}".format(self.a_group_year_parent_2.title_fr + ' [{}]'.format(self.standard_version_2.title_fr))
        results = [res1, res2]
        self.assertCountEqual(
            results,
            [
                first_training_occurence[TRAINING_TITLE_COLUMN],
                second_training_occurence[TRAINING_TITLE_COLUMN]
            ]
        )

    def test_no_white_cells(self):
        dict_to_update = defaultdict(list)
        result = _check_cell_to_color(
            dict_to_update=dict_to_update, learning_unit_yr=self.learning_unit_yr_1, row_number=1
        )
        self.assertListEqual(result[WHITE_FONT], [])

    def test_white_cells_because_second_line_of_usage_of_an_UE(self):
        dict_to_update = defaultdict(list)
        result = _check_cell_to_color(
            dict_to_update=dict_to_update, learning_unit_yr=self.learning_unit_yr_1, row_number=1, training_occurence=2
        )

        first_row_cells_without_training_data = [
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1',
            'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1'
        ]
        self.assertListEqual(result[WHITE_FONT], first_row_cells_without_training_data)

    def test_colored_cells_because_of_proposal(self):    

        dict_to_update = defaultdict(list)
        result = _check_cell_to_color(
            dict_to_update=dict_to_update, learning_unit_yr=self.proposal.learning_unit_year, row_number=1
        )        
        row_colored_because_of_proposal = [
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1',
            'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1', 'AA1', 'AB1', 'AC1'
        ]
        self.assertDictEqual(result, {PROPOSAL_LINE_STYLES.get(self.proposal.type): row_colored_because_of_proposal})

    def test_colored_cells_because_of_proposal_on_second_training_usage(self):    
        proposal = ProposalLearningUnitFactory(
            learning_unit_year=self.learning_unit_yr_1,
            type=proposal_type.ProposalType.MODIFICATION.name,
        )
        dict_to_update = defaultdict(list)
        result = _check_cell_to_color(
            dict_to_update=dict_to_update,
            learning_unit_yr=proposal.learning_unit_year,
            row_number=1,
            training_occurence=2
        )        
        first_row_cells_without_training_data = [
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1',
            'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1'
        ]
        row_colored_because_of_proposal = [
            'Z1', 'AA1', 'AB1', 'AC1'
        ]
        self.assertListEqual(result[WHITE_FONT], first_row_cells_without_training_data)
        self.assertListEqual(result[PROPOSAL_LINE_STYLES.get(proposal.type)], row_colored_because_of_proposal)

    def _get_luy_expected_data(self, luy, a_tutor):
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
            '{} {}'.format(a_tutor.person.last_name.upper(), a_tutor.person.first_name),
            a_tutor.person.email,
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
            "{} ({})".format(self.a_group_year_parent.partial_acronym,
                             "{0:.2f}".format(self.group_element_child.relative_credits)),
            self.a_group_year_parent.acronym,
            self.a_group_year_parent.title_fr + ' [{}]'.format(self.standard_version.title_fr),
            '-'
        ]


def _create_tutor_and_attributions(learning_unit_yr_1: LearningUnitYear) -> Tutor:
    component_lecturing = LearningComponentYearFactory(
        learning_unit_year=learning_unit_yr_1,
        type=learning_component_year_type.LECTURING
    )
    component_practical = LearningComponentYearFactory(
        learning_unit_year=learning_unit_yr_1,
        type=learning_component_year_type.PRACTICAL_EXERCISES
    )

    a_tutor_1 = TutorFactory()

    an_attribution_1 = AttributionNewFactory(
        tutor=a_tutor_1,
        start_year=learning_unit_yr_1.academic_year.year
    )
    AttributionChargeNewFactory(
        learning_component_year=component_lecturing,
        attribution=an_attribution_1,
        allocation_charge=15.0)
    AttributionChargeNewFactory(
        learning_component_year=component_practical,
        attribution=an_attribution_1,
        allocation_charge=5.0)
    return a_tutor_1
