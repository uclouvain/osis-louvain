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
import copy
import datetime
from unittest import mock

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business.learning_unit_proposal import copy_learning_unit_data
from base.business.learning_units.xls_comparison import prepare_xls_content, \
    _get_learning_unit_yrs_on_2_different_years, translate_status, create_xls_comparison, \
    XLS_FILENAME, XLS_DESCRIPTION, learning_unit_titles, WORKSHEET_TITLE, CELLS_MODIFIED_NO_BORDER, DATA, \
    _check_changes_other_than_code_and_year, CELLS_TOP_BORDER, _check_changes, _get_proposal_data, \
    get_representing_string, _get_data_from_initial_data
from base.business.proposal_xls import components_titles, basic_titles, BLANK_VALUE
from base.models.enums.component_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2
from base.models.learning_component_year import LearningComponentYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory
from osis_common.document import xls_build


class TestComparisonXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.old_academic_year = AcademicYearFactory(year=datetime.date.today().year - 2)
        cls.current_academic_year = AcademicYearFactory(year=datetime.date.today().year)
        generatorContainer = GenerateContainer(cls.old_academic_year, cls.current_academic_year)
        cls.previous_learning_unit_year = generatorContainer.generated_container_years[0].learning_unit_year_full
        cls.partim = generatorContainer.generated_container_years[0].learning_unit_year_partim
        cls.learning_unit_year_1 = generatorContainer.generated_container_years[1].learning_unit_year_full
        cls.academic_year = cls.learning_unit_year_1.academic_year
        cls.previous_academic_year = cls.previous_learning_unit_year.academic_year

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(prepare_xls_content([]), {'data': [], CELLS_MODIFIED_NO_BORDER: None, CELLS_TOP_BORDER: None})

    def test_prepare_xls_content_with_data(self):
        learning_unit_years = _get_learning_unit_yrs_on_2_different_years(
            self.previous_academic_year.year,
            [self.learning_unit_year_1]
        )
        data_dict = prepare_xls_content(learning_unit_years)
        data = data_dict.get(DATA)
        self.assertEqual(len(data), 2)
        learning_unit_yr = self.previous_learning_unit_year
        self.assertEqual(data[0][0], learning_unit_yr.acronym)
        self.assertEqual(data[0][1], learning_unit_yr.academic_year.name)
        self.assertEqual(data[0][2], learning_unit_yr.learning_container_year.get_container_type_display())
        self.assertEqual(data[0][3], translate_status(learning_unit_yr.status))
        self.assertEqual(data[0][4], learning_unit_yr.get_subtype_display())
        self.assertEqual(
            data[0][5],
            str(_(learning_unit_yr.get_internship_subtype_display()))
            if learning_unit_yr.internship_subtype else BLANK_VALUE
        )
        self.assertEqual(data[0][6], str(learning_unit_yr.credits))
        self.assertEqual(data[0][7], learning_unit_yr.language.name or BLANK_VALUE)
        self.assertEqual(data[0][8],
                         str(_(learning_unit_yr.get_periodicity_display())) if learning_unit_yr.periodicity else '')
        self.assertEqual(data[0][9], str(_(learning_unit_yr.quadrimester)) or BLANK_VALUE)
        self.assertEqual(data[0][10], str(_(learning_unit_yr.session)) or BLANK_VALUE)
        self.assertEqual(data[0][11], learning_unit_yr.learning_container_year.common_title or BLANK_VALUE)
        self.assertEqual(data[0][12], learning_unit_yr.specific_title or BLANK_VALUE)
        self.assertEqual(data[0][13], learning_unit_yr.learning_container_year.common_title_english or BLANK_VALUE)
        self.assertEqual(data[0][14], learning_unit_yr.specific_title_english or BLANK_VALUE)
        self.assertEqual(data[0][15], learning_unit_yr.requirement_entity.most_recent_acronym or BLANK_VALUE)
        self.assertEqual(data[0][16], learning_unit_yr.allocation_entity.most_recent_acronym or BLANK_VALUE)
        self.assertEqual(data[0][17], learning_unit_yr.learning_container_year.additional_entity_1.most_recent_acronym
                         or BLANK_VALUE)
        self.assertEqual(data[0][18], learning_unit_yr.learning_container_year.additional_entity_2.most_recent_acronym
                         or BLANK_VALUE)
        self.assertEqual(data[0][19], _('Yes') if learning_unit_yr.professional_integration else _('No'))
        if learning_unit_yr.campus:
            self.assertEqual(data[0][20], learning_unit_yr.campus.organization.name)
            self.assertEqual(data[0][21], learning_unit_yr.campus)
        else:
            self.assertEqual(data[0][20], BLANK_VALUE)
            self.assertEqual(data[0][21], BLANK_VALUE)
        self.assertEqual(data[0][22], self.partim.subdivision)
        self.assertEqual(data[0][23], learning_unit_yr.learning_unit.faculty_remark or BLANK_VALUE)
        self.assertEqual(data[0][24], learning_unit_yr.learning_unit.other_remark or BLANK_VALUE)
        self.assertEqual(data[0][25], _('Yes') if learning_unit_yr.learning_container_year.team else _('No'))
        self.assertEqual(data[0][26], _('Yes') if learning_unit_yr.learning_container_year.is_vacant else _('No'))
        self.assertEqual(data[0][27], learning_unit_yr.learning_container_year.get_type_declaration_vacant_display()
                         or BLANK_VALUE)
        self.assertEqual(data[0][28], learning_unit_yr.get_attribution_procedure_display() or BLANK_VALUE)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        create_xls_comparison(self.user, [], None, self.previous_academic_year.year)
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    def test_check_for_changes(self):
        learning_unit_yr_data = [
            ['acronym', '2016-17', 'credits', 'idem'],
            ['acronym 2', '2017-18', 'other credits', 'idem'],
        ]
        # C2 ('C' = third column, '2' = 2nd line)
        self.assertEqual(
            _check_changes_other_than_code_and_year(
                learning_unit_yr_data[0],
                learning_unit_yr_data[1],
                2),
            ['A2', 'C2'])

    def test_learning_unit_titles(self):
        self.assertEqual(
            learning_unit_titles(),
            basic_titles() + components_titles()
        )


class TestPropositionComparisonXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.current_academic_year = AcademicYearFactory(year=datetime.date.today().year)
        generatorContainer = GenerateContainer(cls.current_academic_year, cls.current_academic_year)
        cls.partim = generatorContainer.generated_container_years[0].learning_unit_year_partim
        cls.learning_unit_year_1 = generatorContainer.generated_container_years[0].learning_unit_year_full
        cls.entity_1 = generatorContainer.entities[0]
        cls.entity_version_1 = EntityVersionFactory(entity=cls.entity_1, acronym="AGRO")
        cls.entity_2 = generatorContainer.entities[1]
        cls.entity_version_2 = EntityVersionFactory(entity=cls.entity_2, acronym="DRT")

        cls.learning_unit_year_1.entities = {REQUIREMENT_ENTITY: cls.entity_version_1,
                                             ALLOCATION_ENTITY: cls.entity_version_1,
                                             ADDITIONAL_REQUIREMENT_ENTITY_1: cls.entity_version_2}
        cls.learning_unit_year_1.learning_container_year.requirement_entity = cls.entity_version_1.entity
        cls.learning_unit_year_1.learning_container_year.allocation_entity = cls.entity_version_1.entity
        cls.learning_unit_year_1.learning_container_year.additional_entity_1 = cls.entity_version_2.entity
        cls.learning_unit_year_1.learning_container_year.additional_entity_2 = None

        cls.original_learning_unit_year_1 = copy.deepcopy(cls.learning_unit_year_1)

        cls.academic_year = cls.learning_unit_year_1.academic_year
        cls.proposal = ProposalLearningUnitFactory(learning_unit_year=cls.learning_unit_year_1,
                                                   initial_data={"learning_unit": {"faculty_remark": "First remark"}})

    def test_get_proposal_data(self):
        practical_component = LearningComponentYear.objects.filter(
            learning_unit_year=self.learning_unit_year_1,
            type=PRACTICAL_EXERCISES
        ).first()
        lecturing_component = LearningComponentYear.objects.filter(
            learning_unit_year=self.learning_unit_year_1,
            type=LECTURING
        ).first()

        data = _get_proposal_data(self.learning_unit_year_1)

        self.assertEqual(data[0], _('Proposal'))
        self.assertEqual(data[1], self.learning_unit_year_1.acronym)
        self.assertEqual(data[2], "{}   ({} {})".format(self.learning_unit_year_1.academic_year.name,
                                                        _('End').lower(),
                                                        self.learning_unit_year_1.learning_unit.end_year.name)
                         )
        self.assertEqual(data[3], self.learning_unit_year_1.learning_container_year.get_container_type_display())
        self.assertEqual(data[4], translate_status(self.learning_unit_year_1.status))
        self.assertEqual(data[5], self.learning_unit_year_1.get_subtype_display())
        self.assertEqual(data[6],
                         str(_(self.learning_unit_year_1.get_internship_subtype_display()))
                         if self.learning_unit_year_1.internship_subtype else '-')
        self.assertEqual(data[7], str(self.learning_unit_year_1.credits))
        self.assertEqual(data[8], self.learning_unit_year_1.language.name or BLANK_VALUE)
        self.assertEqual(data[9], str(_(self.learning_unit_year_1.get_periodicity_display())) or BLANK_VALUE)
        self.assertEqual(data[10], str(_(self.learning_unit_year_1.quadrimester)) or BLANK_VALUE)
        self.assertEqual(data[11], str(_(self.learning_unit_year_1.session)) or BLANK_VALUE)
        self.assertEqual(data[12], self.learning_unit_year_1.learning_container_year.common_title or BLANK_VALUE)
        self.assertEqual(data[13], self.learning_unit_year_1.specific_title or BLANK_VALUE)
        self.assertEqual(data[14], self.learning_unit_year_1.learning_container_year.common_title_english
                         or BLANK_VALUE)
        self.assertEqual(data[15], self.learning_unit_year_1.specific_title_english or BLANK_VALUE)

        self.assertEqual(data[16], self.learning_unit_year_1.entities.get(REQUIREMENT_ENTITY).acronym or BLANK_VALUE)
        self.assertEqual(data[17], self.learning_unit_year_1.entities.get(ALLOCATION_ENTITY).acronym or BLANK_VALUE)
        self.assertEqual(data[18], self.learning_unit_year_1.entities.get(ADDITIONAL_REQUIREMENT_ENTITY_1).acronym
                         or BLANK_VALUE)
        self.assertEqual(data[19], BLANK_VALUE)
        self.assertEqual(data[20], _('Yes') if self.learning_unit_year_1.professional_integration else _('No'))
        if self.learning_unit_year_1.campus:
            self.assertEqual(data[21], self.learning_unit_year_1.campus.organization.name)
            self.assertEqual(data[22], self.learning_unit_year_1.campus)
        else:
            self.assertEqual(data[21], BLANK_VALUE)
            self.assertEqual(data[22], BLANK_VALUE)
        self.assertEqual(data[23], self.learning_unit_year_1.learning_unit.faculty_remark or BLANK_VALUE)
        self.assertEqual(data[24], self.learning_unit_year_1.learning_unit.other_remark or BLANK_VALUE)
        self.assertEqual(data[25], _('Yes') if self.learning_unit_year_1.learning_container_year.team else _('No'))
        self.assertEqual(data[26], _('Yes') if self.learning_unit_year_1.learning_container_year.is_vacant else _('No'))
        self.assertEqual(data[27],
                         self.learning_unit_year_1.learning_container_year.get_type_declaration_vacant_display()
                         or BLANK_VALUE)
        self.assertEqual(data[28], self.learning_unit_year_1.get_attribution_procedure_display() or BLANK_VALUE)

        self.assertEqual(data[29], lecturing_component.hourly_volume_total_annual or BLANK_VALUE)
        self.assertEqual(data[30], lecturing_component.hourly_volume_partial_q1 or BLANK_VALUE)
        self.assertEqual(data[31], lecturing_component.hourly_volume_partial_q2 or BLANK_VALUE)
        self.assertEqual(data[32], lecturing_component.real_classes or BLANK_VALUE)
        self.assertEqual(data[33], lecturing_component.planned_classes or BLANK_VALUE)
        self.assertEqual(data[38], practical_component.hourly_volume_total_annual or BLANK_VALUE)
        self.assertEqual(data[39], practical_component.hourly_volume_partial_q1 or BLANK_VALUE)
        self.assertEqual(data[40], practical_component.hourly_volume_partial_q2 or BLANK_VALUE)
        self.assertEqual(data[41], practical_component.real_classes or BLANK_VALUE)
        self.assertEqual(data[42], practical_component.planned_classes or BLANK_VALUE)

    def test_check_changes(self):
        line_number = 0
        # First 2 columns are unmutable
        self.assertEqual(_check_changes(['elt1', 'elt2', 'elt3', 'elt4'],
                                        ['elt1', 'elt2 bis', 'elt3 bis', 'elt4'],
                                        line_number), ['C{}'.format(line_number)])

    def test_get_represen_string(self):
        self.assertEqual(get_representing_string(None), BLANK_VALUE)
        self.assertEqual(get_representing_string(""), BLANK_VALUE)
        self.assertEqual(get_representing_string("test"), "test")

    def test_get_data_from_initial_data(self):
        practical_component = LearningComponentYear.objects.filter(
            learning_unit_year=self.learning_unit_year_1,
            type=PRACTICAL_EXERCISES
        ).first()
        lecturing_component = LearningComponentYear.objects.filter(
            learning_unit_year=self.learning_unit_year_1,
            type=LECTURING
        ).first()

        actual_data = copy_learning_unit_data(self.learning_unit_year_1)
        self.learning_unit_year_1.proposallearningunit.initial_data = actual_data
        self.learning_unit_year_1.proposallearningunit.save()

        data = _get_data_from_initial_data(self.learning_unit_year_1.proposallearningunit.initial_data, True)

        to_test = []
        to_test.append((data[0], _('Initial data')))
        to_test.append((data[1], self.original_learning_unit_year_1.acronym))
        to_test.append((data[2], "{}   ({} {})".format(self.original_learning_unit_year_1.academic_year.name,
                                                       _('End').lower(),
                                                       self.original_learning_unit_year_1.learning_unit.end_year)))  # Attention, c'est l'id
        to_test.append((data[3],
                        self.original_learning_unit_year_1.learning_container_year.get_container_type_display()))
        to_test.append((data[4], translate_status(self.original_learning_unit_year_1.status)))
        to_test.append((data[5], self.original_learning_unit_year_1.get_subtype_display()))
        to_test.append((data[6],
                        str(_(self.original_learning_unit_year_1.get_internship_subtype_display()))
                        if self.original_learning_unit_year_1.internship_subtype else '-'))
        to_test.append((data[7], str(self.original_learning_unit_year_1.credits)))
        to_test.append((data[8], self.original_learning_unit_year_1.language.name or BLANK_VALUE))
        to_test.append((data[9], str(_(self.original_learning_unit_year_1.get_periodicity_display())) or BLANK_VALUE))
        to_test.append((data[10], str(_(self.original_learning_unit_year_1.quadrimester)) or BLANK_VALUE))
        to_test.append((data[11], str(_(self.original_learning_unit_year_1.session)) or BLANK_VALUE))
        to_test.append((data[12],
                        self.original_learning_unit_year_1.learning_container_year.common_title or BLANK_VALUE))
        to_test.append((data[13], self.original_learning_unit_year_1.specific_title or BLANK_VALUE))
        to_test.append((data[14], self.original_learning_unit_year_1.learning_container_year.common_title_english
                        or BLANK_VALUE))
        to_test.append((data[15], self.original_learning_unit_year_1.specific_title_english or BLANK_VALUE))

        to_test.append((data[16],
                        self.original_learning_unit_year_1.entities.get(REQUIREMENT_ENTITY).acronym or BLANK_VALUE))
        to_test.append((data[17],
                        self.original_learning_unit_year_1.entities.get(ALLOCATION_ENTITY).acronym or BLANK_VALUE))
        to_test.append((data[18],
                        self.original_learning_unit_year_1.entities.get(ADDITIONAL_REQUIREMENT_ENTITY_1).acronym
                        if self.original_learning_unit_year_1.entities.get(ADDITIONAL_REQUIREMENT_ENTITY_1)
                        else BLANK_VALUE))
        to_test.append((data[19],
                        self.original_learning_unit_year_1.entities.get(ADDITIONAL_REQUIREMENT_ENTITY_2).acronym
                        if self.original_learning_unit_year_1.entities.get(ADDITIONAL_REQUIREMENT_ENTITY_2)
                        else BLANK_VALUE))
        to_test.append((data[20], _('Yes') if self.original_learning_unit_year_1.professional_integration else _('No')))
        if self.learning_unit_year_1.campus:
            to_test.append((data[21], self.original_learning_unit_year_1.campus.organization.name))
            to_test.append((data[22], self.original_learning_unit_year_1.campus))
        else:
            to_test.append((data[21], BLANK_VALUE))
            to_test.append((data[22], BLANK_VALUE))
        to_test.append((data[23], self.original_learning_unit_year_1.learning_unit.faculty_remark or BLANK_VALUE))
        to_test.append((data[24], self.original_learning_unit_year_1.learning_unit.other_remark or BLANK_VALUE))
        to_test.append((data[25],
                        _('Yes') if self.original_learning_unit_year_1.learning_container_year.team else _('No')))
        to_test.append((data[26],
                        _('Yes') if self.original_learning_unit_year_1.learning_container_year.is_vacant else _('No')))
        to_test.append((data[27],
                        self.original_learning_unit_year_1.learning_container_year.get_type_declaration_vacant_display()
                        or BLANK_VALUE))
        to_test.append((data[28],
                        self.original_learning_unit_year_1.get_attribution_procedure_display() or BLANK_VALUE))

        to_test.append((data[29], lecturing_component.hourly_volume_total_annual or BLANK_VALUE))
        to_test.append((data[30], lecturing_component.hourly_volume_partial_q1 or BLANK_VALUE))
        to_test.append((data[31], lecturing_component.hourly_volume_partial_q2 or BLANK_VALUE))
        to_test.append((data[32], lecturing_component.real_classes or BLANK_VALUE))
        to_test.append((data[33], lecturing_component.planned_classes or BLANK_VALUE))
        to_test.append((data[38], practical_component.hourly_volume_total_annual or BLANK_VALUE))
        to_test.append((data[39], practical_component.hourly_volume_partial_q1 or BLANK_VALUE))
        to_test.append((data[40], practical_component.hourly_volume_partial_q2 or BLANK_VALUE))
        to_test.append((data[41], practical_component.real_classes or BLANK_VALUE))
        to_test.append((data[42], practical_component.planned_classes or BLANK_VALUE))

        for (i, (result, expected)) in enumerate(to_test):
            with self.subTest(i):
                self.assertEqual(expected, result)


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: learning_unit_titles(),
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.COLORED_ROWS: None,
            xls_build.ROW_HEIGHT: None,
        }]
    }
