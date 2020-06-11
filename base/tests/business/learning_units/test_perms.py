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
from django.test.utils import override_settings

from base.business.learning_units.perms import MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR, \
    is_eligible_for_modification, can_update_learning_achievement, is_eligible_to_update_learning_unit_pedagogy
from base.business.learning_units.perms import is_eligible_to_modify_end_year_by_proposal, \
    is_eligible_to_modify_by_proposal, MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_calendar import generate_creation_or_end_date_proposal_calendars, \
    generate_modification_transformation_proposal_calendars
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import FacultyManagerForUEFactory, AdministrativeManagerFactory, CentralManagerForUEFactory


class TestPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit = LearningUnitFactory()
        cls.current_academic_year = create_current_academic_year()
        cls.next_academic_yr = AcademicYearFactory(year=cls.current_academic_year.year+1)
        academic_years = [cls.current_academic_year, cls.next_academic_yr]
        cls.lcy = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=EntityVersionFactory().entity
        )
        cls.central_manager = CentralManagerForUEFactory('can_edit_learningunit_pedagogy')
        cls.luy = LearningUnitYearFactory(
            learning_unit=cls.learning_unit,
            academic_year=cls.current_academic_year,
            learning_container_year=cls.lcy,
        )
        cls.central_manager.linked_entities = [cls.lcy.requirement_entity.id]

        generate_creation_or_end_date_proposal_calendars(academic_years)
        generate_modification_transformation_proposal_calendars(academic_years)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_not_is_eligible_to_modify_end_year_by_proposal(self, mock_perm):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        person_faculty_manager = FacultyManagerForUEFactory()

        with self.assertRaises(PermissionDenied) as perm_ex:
            is_eligible_to_modify_end_year_by_proposal(learning_unit_yr, person_faculty_manager, True)
            self.assertEqual('{}'.format(perm_ex.exception), MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_is_eligible_to_modify_end_year_by_proposal(self, mock_perm):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        person_faculty_manager = FacultyManagerForUEFactory()
        self.assertTrue(is_eligible_to_modify_end_year_by_proposal(learning_unit_yr, person_faculty_manager, True))

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_not_is_eligible_to_modify_by_proposal(self, mock_perm):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        person_faculty_manager = FacultyManagerForUEFactory()

        with self.assertRaises(PermissionDenied) as perm_ex:
            is_eligible_to_modify_by_proposal(learning_unit_yr, person_faculty_manager, True)
            self.assertEqual('{}'.format(perm_ex.exception), MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_create_modification_proposal", return_value=True)
    def test_is_eligible_to_modify_by_proposal(self, mock_perm):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        person_faculty_manager = FacultyManagerForUEFactory()
        self.assertTrue(is_eligible_to_modify_by_proposal(learning_unit_yr, person_faculty_manager, True))

    def test_is_not_eligible_to_modify_cause_user_is_administrative_manager(self):
        administrative_manager = AdministrativeManagerFactory()
        self.assertFalse(is_eligible_for_modification(self.luy, administrative_manager))

    @mock.patch('waffle.models.Flag.is_active_for_user', return_value=True)
    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=2018)
    def test_is_not_eligible_to_update_learning_achievement_cause_before_2018(self, mock_flag):
        self.luy.academic_year = AcademicYearFactory(year=2015)
        self.assertFalse(can_update_learning_achievement(self.luy, self.central_manager))

    @mock.patch('waffle.models.Flag.is_active_for_user', return_value=True)
    def test_is_eligible_to_update_learning_achievement_after_2017(self, mock_flag):
        self.luy.academic_year = AcademicYearFactory(year=2019)
        self.assertTrue(can_update_learning_achievement(self.luy, self.central_manager))

    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=2018)
    def test_is_not_eligible_to_update_learning_pedagogy_cause_before_2018(self):
        self.luy.academic_year = AcademicYearFactory(year=2015)
        self.assertFalse(is_eligible_to_update_learning_unit_pedagogy(self.luy, self.central_manager))

    def test_is_eligible_to_update_learning_pedagogy_after_2017(self):
        self.luy.academic_year = AcademicYearFactory(year=2019)
        self.assertTrue(is_eligible_to_update_learning_unit_pedagogy(self.luy, self.central_manager))
