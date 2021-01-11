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
from django.test import TestCase

from base.business import event_perms
from base.models.enums import academic_calendar_type
from base.tests.factories import person as person_factory
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year
from education_group.tests.factories.auth.central_manager import CentralManagerFactory as OFCentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory as OFFacultyManagerFactory
from learning_unit.tests.factories.central_manager import CentralManagerFactory as UECentralManagerFactory
from learning_unit.tests.factories.faculty_manager import FacultyManagerFactory as UEFacultyManagerFactory


class TestEventPermPropositionsCreationEndDate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_CENTRAL_MANAGERS,
            data_year=cls.current_academic_year
        )
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_FACULTY_MANAGERS,
            data_year=cls.current_academic_year
        )

    def test_event_perm_creation_end_date_proposal_regular_user(self):
        person = person_factory.PersonFactory()
        event_perm = event_perms.generate_event_perm_creation_end_date_proposal(person)
        self.assertFalse(event_perm.is_open())

    def test_event_perm_creation_end_date_proposal_central_manager(self):
        central_manager = OFCentralManagerFactory()
        event_perm = event_perms.generate_event_perm_creation_end_date_proposal(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_creation_end_date_proposal_faculty_manager(self):
        faculty_manager = OFFacultyManagerFactory()
        event_perm = event_perms.generate_event_perm_creation_end_date_proposal(faculty_manager.person)
        self.assertTrue(event_perm.is_open())


class TestEventPermPropositionsModificationTransformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_CENTRAL_MANAGERS,
            data_year=cls.current_academic_year
        )
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_FACULTY_MANAGERS,
            data_year=cls.current_academic_year
        )

    def test_event_perm_modification_transformation_proposal_regular_user(self):
        person = person_factory.PersonFactory()
        event_perm = event_perms.generate_event_perm_modification_transformation_proposal(person)
        self.assertFalse(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_central_manager(self):
        central_manager = UECentralManagerFactory()
        event_perm = event_perms.generate_event_perm_modification_transformation_proposal(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_faculty_manager(self):
        faculty_manager = UEFacultyManagerFactory()
        event_perm = event_perms.generate_event_perm_modification_transformation_proposal(faculty_manager.person)
        self.assertTrue(event_perm.is_open())


class TestEventPermLearningUnitEdition(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.LEARNING_UNIT_EDITION_FACULTY_MANAGERS,
            data_year=cls.current_academic_year
        )
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.LEARNING_UNIT_EDITION_CENTRAL_MANAGERS,
            data_year=cls.current_academic_year
        )

    def test_event_perm_modification_transformation_proposal_regular_user(self):
        person = person_factory.PersonFactory()
        event_perm = event_perms.generate_event_perm_learning_unit_edition(person)
        self.assertFalse(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_central_manager(self):
        central_manager = UECentralManagerFactory()
        event_perm = event_perms.generate_event_perm_learning_unit_edition(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_faculty_manager(self):
        faculty_manager = UEFacultyManagerFactory()
        event_perm = event_perms.generate_event_perm_learning_unit_edition(faculty_manager.person)
        self.assertTrue(event_perm.is_open())
