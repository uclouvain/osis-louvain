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
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from base.business.learning_units.perms import MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR
from base.business.learning_units.perms import is_eligible_to_modify_end_year_by_proposal, \
    is_eligible_to_modify_by_proposal, MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR, is_eligible_for_modification
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import FacultyManagerFactory, CatalogViewerFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


class TestPerms(TestCase):

    def setUp(self):
        self.learning_unit = LearningUnitFactory()
        self.current_academic_year = create_current_academic_year()
        self.next_academic_yr = AcademicYearFactory(year=self.current_academic_year.year+1)
        self.lcy = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                container_type=learning_container_year_types.COURSE)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_not_is_eligible_to_modify_end_year_by_proposal(self, mock_perm):

        lu = LearningUnitFactory(existing_proposal_in_epc=False)
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_unit=lu,
            learning_container_year=self.lcy
        )
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_yr)
        person_faculty_manager = FacultyManagerFactory()

        with self.assertRaises(PermissionDenied) as perm_ex:
            is_eligible_to_modify_end_year_by_proposal(learning_unit_yr,
                                                       person_faculty_manager,
                                                       True)
            self.assertEqual('{}'.format(perm_ex.exception), MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_is_eligible_to_modify_end_year_by_proposal(self, mock_perm):
        lu = LearningUnitFactory(existing_proposal_in_epc=False)
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_unit=lu,
            learning_container_year=self.lcy
        )
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_yr)
        person_faculty_manager = FacultyManagerFactory()
        self.assertTrue(is_eligible_to_modify_end_year_by_proposal(learning_unit_yr,
                                                                   person_faculty_manager,
                                                                   True))

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_not_is_eligible_to_modify_by_proposal(self, mock_perm):

        lu = LearningUnitFactory(existing_proposal_in_epc=False)
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_unit=lu,
            learning_container_year=self.lcy
        )
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_yr)
        person_faculty_manager = FacultyManagerFactory()

        with self.assertRaises(PermissionDenied) as perm_ex:
            is_eligible_to_modify_by_proposal(
                learning_unit_yr,
                person_faculty_manager,
                True
            )
            self.assertEqual('{}'.format(perm_ex.exception), MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_is_eligible_to_modify_by_proposal(self, mock_perm):
        lu = LearningUnitFactory(existing_proposal_in_epc=False)
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_unit=lu,
            learning_container_year=self.lcy
        )
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_yr)
        person_faculty_manager = FacultyManagerFactory()
        self.assertTrue(is_eligible_to_modify_by_proposal(
            learning_unit_yr,
            person_faculty_manager,
            True
        ))

    def test_is_not_eligible_to_modify_cause_user_is_catalog_viewer(self):
        cv = CatalogViewerFactory()
        luy = LearningUnitYearFactory(learning_unit=self.learning_unit, learning_container_year=self.lcy)
        self.assertFalse(is_eligible_for_modification(luy, cv))
