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
from unittest import mock

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business import proposal_xls
from base.business.learning_unit_year_with_context import append_latest_entities
from base.business.learning_units.xls_comparison import prepare_xls_content_for_comparison
from base.business.proposal_xls import XLS_DESCRIPTION, XLS_FILENAME, WORKSHEET_TITLE, basic_titles_part_1, \
    basic_titles_part_2, components_titles, basic_titles
from base.models.enums import entity_type
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_year_periodicity import PERIODICITY_TYPES
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory
from base.tests.forms.test_learning_unit_proposal import build_initial_data
from osis_common.document import xls_build

ACRONYM_ALLOCATION = 'INFO'
ACRONYM_REQUIREMENT = 'DRT'


class TestProposalXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.learning_unit = LearningUnitFactory(start_year__year=1900)

        cls.l_container_year = LearningContainerYearFactory(acronym="LBIR1212", academic_year=cls.academic_year)

        cls.user = UserFactory()

    def setUp(self):
        self.l_unit_yr_1 = LearningUnitYearFactory(acronym="LBIR1212", learning_container_year=self.l_container_year,
                                                   academic_year=self.academic_year,
                                                   subtype=learning_unit_year_subtypes.FULL,
                                                   credits=10)
        entity_requirement_ver = EntityVersionFactory(acronym=ACRONYM_REQUIREMENT,
                                                      entity=EntityFactory())
        self.l_unit_yr_1.entity_requirement = entity_requirement_ver.acronym
        entity_allocation_ver = EntityVersionFactory(acronym=ACRONYM_ALLOCATION, entity=EntityFactory())
        self.l_unit_yr_1.entity_allocation = entity_allocation_ver.acronym
        entity_vr = EntityVersionFactory(acronym='ESPO')

        self.proposal_1 = ProposalLearningUnitFactory(learning_unit_year=self.l_unit_yr_1,
                                                      entity=entity_vr.entity)
        self._set_entities()

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(proposal_xls.prepare_xls_content([]), [])
        proposals_data = prepare_xls_content_for_comparison([])
        self.assertEqual(proposals_data['data'], [])

    def test_prepare_xls_content_with_data(self):
        proposals_data = proposal_xls.prepare_xls_content([self.proposal_1.learning_unit_year])
        self.assertEqual(len(proposals_data), 1)
        self.assertEqual(proposals_data[0], self._get_xls_data())

    def test_prepare_xls_comparison_content_with_data_without_initial_data(self):
        proposals_data = prepare_xls_content_for_comparison([self.l_unit_yr_1])
        self.assertEqual(len(proposals_data['data']), 1)

    def test_prepare_xls_comparison_content_with_data_with_initial_data(self):
        self.proposal_1.initial_data = build_initial_data(self.l_unit_yr_1, self.entity_version.entity)
        self.proposal_1.save()
        proposals_data = prepare_xls_content_for_comparison([self.l_unit_yr_1])
        self.assertEqual(len(proposals_data['data']), 2)

    def test_basic_titles_part_1(self):
        self.assertEqual(
            basic_titles_part_1(),
            [
                str(_('Code')),
                str(_('Ac yr.')),
                str(_('Type')),
                str(_('Active')),
                str(_('Subtype')),
                str(_('Internship subtype')),
                str(_('Credits')),
                str(_('Language')),
                str(_('Periodicity')),
                str(_('Quadrimester')),
                str(_('Session derogation')),
                str(_('Common title')),
                str(_('French title proper')),
                str(_('Common English title')),
                str(_('English title proper')),
                str(_('Req. Entities')),
                str(_('Alloc. Ent.')),
                str(_('Add. requ. ent. 1')),
                str(_('Add. requ. ent. 2')),
                str(_('Profes. integration')),
                str(_('Institution')),
                str(_('Learning location')),
            ]
        )

    def test_basic_titles_part_2(self):
        self.assertEqual(
            basic_titles_part_2(),
            [
                str(_("Faculty remark (unpublished)")),
                str(_("Other remark (intended for publication)")),
                str(_("Team management")),
                str(_("Vacant")),
                str(_("Decision")),
                str(_("Procedure")),
            ]
        )

    def test_components_titles(self):
        self.assertEqual(
            components_titles(),
            [
                "PM {}".format(_('Vol. Q1')),
                "PM {}".format(_('Vol. Q2')),
                "PM {}".format(_('Vol. annual')),
                "PM {}".format(_('Real classes')),
                "PM {}".format(_('Planned classes')),
                "PM {}".format(_('Vol. global')),
                "PM {}".format(_('Req. Entities')),
                "PM {}".format(_('Add. requ. ent. 1')),
                "PM {}".format(_('Add. requ. ent. 2')),
                "PP {}".format(_('Vol. Q1')),
                "PP {}".format(_('Vol. Q2')),
                "PP {}".format(_('Vol. annual')),
                "PP {}".format(_('Real classes')),
                "PP {}".format(_('Planned classes')),
                "PP {}".format(_('Vol. global')),
                "PP {}".format(_('Req. Entities')),
                "PP {}".format(_('Add. requ. ent. 1')),
                "PP {}".format(_('Add. requ. ent. 2'))
            ]
        )

    def test_basic_titles(self):
        self.assertEqual(
            basic_titles(),
            basic_titles_part_1() + [str(_('Partims'))] + basic_titles_part_2()
        )

    def _get_xls_data(self):
        return [self.l_unit_yr_1.entity_requirement,
                self.proposal_1.learning_unit_year.acronym,
                self.proposal_1.learning_unit_year.complete_title,
                self.proposal_1.learning_unit_year.learning_container_year.get_container_type_display(),
                self.proposal_1.get_type_display(),
                self.proposal_1.get_state_display(),
                self.proposal_1.folder,
                self.proposal_1.learning_unit_year.learning_container_year.get_type_declaration_vacant_display(),
                dict(PERIODICITY_TYPES)[self.proposal_1.learning_unit_year.periodicity],
                self.proposal_1.learning_unit_year.credits,
                self.l_unit_yr_1.entity_allocation,
                self.proposal_1.date.strftime('%d-%m-%Y')]

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        proposal_xls.create_xls(self.user, [], None)
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_a_learning_unit(self, mock_generate_xls):
        proposal_xls.create_xls(self.user, [self.proposal_1.learning_unit_year], None)
        xls_data = [self._get_xls_data()]
        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    def _set_entities(self):
        today = datetime.date.today()
        an_entity = EntityFactory(organization=OrganizationFactory(type=MAIN))
        self.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL,
                                                   start_date=today.replace(year=1900),
                                                   end_date=None)

        self.l_unit_yr_1.learning_container_year.requirement_entity = self.entity_version.entity
        self.l_unit_yr_1.learning_container_year.allocation_entity = self.entity_version.entity
        self.l_unit_yr_1.learning_container_year.save()

        append_latest_entities(self.proposal_1.learning_unit_year)


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: proposal_xls.PROPOSAL_TITLES,
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.FONT_ROWS: None,
            xls_build.ROW_HEIGHT: None,
        }]
    }
