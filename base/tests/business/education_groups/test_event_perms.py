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
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business import event_perms
from base.models.education_group_year import EducationGroupYear
from base.models.enums import academic_calendar_type
from base.tests.factories import person as person_factory
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory


class TestEventPermEducationGroupEditionPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
                                    academic_year=cls.current_academic_year,
                                    data_year=cls.current_academic_year)
        OpenAcademicCalendarFactory(reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
                                    academic_year__year=cls.current_academic_year.year + 1,
                                    data_year__year=cls.current_academic_year.year + 1)

    def test_is_open_for_spec_egy(self):
        egy = TrainingFactory(academic_year=self.current_academic_year)
        self.assertTrue(event_perms.EventPermEducationGroupEdition(obj=egy).is_open())

    def test_is_open_other_rules(self):
        self.assertTrue(event_perms.EventPermEducationGroupEdition().is_open())


class TestEventPermEducationGroupEditionPermsNotOpen(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()

    def test_is_not_open_for_spec_egy_without_exception_raise(self):
        egy = TrainingFactory(academic_year=self.current_academic_year)
        self.assertFalse(event_perms.EventPermEducationGroupEdition(obj=egy, raise_exception=False).is_open())

    def test_is_not_open_for_spec_egy_with_exception_raise(self):
        egy = TrainingFactory(academic_year=self.current_academic_year)
        expected_exception_message = str(_("This education group is not editable during this period."))
        with self.assertRaisesMessage(PermissionDenied, expected_exception_message):
            event_perms.EventPermEducationGroupEdition(obj=egy, raise_exception=True).is_open()

    def test_is_not_open_other_rules(self):
        self.assertFalse(event_perms.EventPermEducationGroupEdition().is_open())


class TestEventPermInit(TestCase):
    def test_init_obj_matches_model(self):
        egy = TrainingFactory()
        event_perms.EventPermEducationGroupEdition(obj=egy, raise_exception=False)

    def test_init_obj_dont_match_model(self):
        luy = LearningUnitYearFactory()
        expected_exception_message = "The provided obj must be a {}".format(EducationGroupYear.__name__)
        with self.assertRaisesMessage(AttributeError, expected_exception_message):
            event_perms.EventPermEducationGroupEdition(obj=luy, raise_exception=False)


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
        central_manager = CentralManagerFactory()
        event_perm = event_perms.generate_event_perm_creation_end_date_proposal(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_creation_end_date_proposal_faculty_manager(self):
        faculty_manager = FacultyManagerFactory()
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
        central_manager = CentralManagerFactory()
        event_perm = event_perms.generate_event_perm_modification_transformation_proposal(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_faculty_manager(self):
        faculty_manager = FacultyManagerFactory()
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
        central_manager = CentralManagerFactory()
        event_perm = event_perms.generate_event_perm_learning_unit_edition(central_manager.person)
        self.assertTrue(event_perm.is_open())

    def test_event_perm_modification_transformation_proposal_faculty_manager(self):
        faculty_manager = FacultyManagerFactory()
        event_perm = event_perms.generate_event_perm_learning_unit_edition(faculty_manager.person)
        self.assertTrue(event_perm.is_open())
