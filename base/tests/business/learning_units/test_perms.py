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

from django.test import TestCase
from django.test.utils import override_settings

from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_calendar import generate_proposal_calendars, generate_learning_unit_edition_calendars
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import AdministrativeManagerFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from learning_unit.tests.factories.central_manager import CentralManagerFactory
from learning_unit.tests.factories.faculty_manager import FacultyManagerFactory


@override_settings(YEAR_LIMIT_LUE_MODIFICATION=2018)
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
        cls.central_manager = CentralManagerFactory(entity=cls.lcy.requirement_entity)
        cls.luy = LearningUnitYearFactory(
            learning_unit=cls.learning_unit,
            academic_year=cls.current_academic_year,
            learning_container_year=cls.lcy,
        )
        cls.central_manager.linked_entities = [cls.lcy.requirement_entity.id]

        generate_proposal_calendars(academic_years)
        generate_learning_unit_edition_calendars(academic_years)

    def test_not_is_eligible_to_modify_end_year_by_proposal(self):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        faculty_manager = FacultyManagerFactory(entity=self.lcy.requirement_entity)
        self.assertFalse(faculty_manager.person.user.has_perm('base.can_propose_learning_unit', learning_unit_yr))

    def test_is_eligible_to_modify_end_year_by_proposal(self):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        faculty_manager = FacultyManagerFactory(entity=self.lcy.requirement_entity)
        self.assertTrue(faculty_manager.person.user.has_perm('base.can_propose_learningunit', learning_unit_yr))

    def test_not_is_eligible_to_modify_by_proposal(self):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        faculty_manager = FacultyManagerFactory()

        self.assertFalse(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', learning_unit_yr))

    def test_is_eligible_to_modify_by_proposal(self):
        learning_unit_yr = LearningUnitYearFactory(
            academic_year=self.next_academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year=self.lcy
        )
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_yr)
        faculty_manager = FacultyManagerFactory(entity=self.lcy.requirement_entity)

        self.assertTrue(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', learning_unit_yr))

    def test_is_not_eligible_to_modify_cause_user_is_administrative_manager(self):
        administrative_manager = AdministrativeManagerFactory()
        self.assertFalse(administrative_manager.user.has_perm('base.can_edit_learningunit', self.luy))

    def test_is_not_eligible_to_update_learning_achievement_cause_before_2018(self):
        self.luy.academic_year = AcademicYearFactory(year=2015)
        self.assertFalse(self.central_manager.person.user.has_perm('base.can_update_learning_achievement', self.luy))

    def test_is_eligible_to_update_learning_achievement_after_2017(self):
        academic_year = AcademicYearFactory(year=2019)
        self.luy.academic_year = academic_year
        generate_learning_unit_edition_calendars([academic_year])
        self.assertTrue(self.central_manager.person.user.has_perm('base.can_update_learning_achievement', self.luy))

    def test_is_not_eligible_to_update_learning_pedagogy_cause_before_2018(self):
        self.luy.academic_year = AcademicYearFactory(year=2015)
        self.assertFalse(is_eligible_to_update_learning_unit_pedagogy(self.luy, self.central_manager.person))

    def test_is_eligible_to_update_learning_pedagogy_after_2017(self):
        academic_year = AcademicYearFactory(year=2019)
        self.luy.academic_year = academic_year
        generate_learning_unit_edition_calendars([academic_year])
        self.assertTrue(is_eligible_to_update_learning_unit_pedagogy(self.luy, self.central_manager.person))
