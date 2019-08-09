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
import datetime

from django.contrib.auth.models import Group
from django.http import Http404
from django.test import TestCase
from django.utils import timezone

from base.business.institution import find_summary_course_submission_dates_for_entity_version, \
    can_user_edit_educational_information_submission_dates_for_entity
from base.models.enums import academic_calendar_type
from base.models.enums.groups import FACULTY_MANAGER_GROUP
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_calendar import EntityCalendarFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group import FacultyManagerGroupFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class FindSummaryCourseSubmissionDatesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.parent_entity = EntityFactory()
        cls.child_entity = EntityFactory()
        cls.child_entity_bis = EntityFactory()
        cls.academic_calendar = AcademicCalendarFactory(academic_year=cls.current_academic_year,
                                                        reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        cls.parent_entity_version = EntityVersionFactory(start_date=cls.current_academic_year.start_date,
                                                         end_date=cls.current_academic_year.end_date,
                                                         entity=cls.parent_entity)
        cls.child_entity_version = EntityVersionFactory(start_date=cls.current_academic_year.start_date,
                                                        end_date=cls.current_academic_year.end_date,
                                                        entity=cls.child_entity,
                                                        parent=cls.parent_entity)
        cls.child_entity_version_bis = EntityVersionFactory(start_date=cls.current_academic_year.start_date,
                                                            end_date=cls.current_academic_year.end_date,
                                                            entity=cls.child_entity_bis,
                                                            parent=cls.parent_entity)
        cls.entity_version_without_entity_calendar = EntityVersionFactory(
            start_date=cls.current_academic_year.start_date,
            end_date=cls.current_academic_year.end_date
        )
        cls.parent_entity_calendar = EntityCalendarFactory(
            academic_calendar=cls.academic_calendar,
            entity=cls.parent_entity,
            start_date=timezone.now() - timezone.timedelta(days=40),
            end_date=timezone.now() + timezone.timedelta(days=20),
        )
        cls.child_entity_calendar_bis = EntityCalendarFactory(
            academic_calendar=cls.academic_calendar,
            entity=cls.child_entity_bis,
            start_date=cls.parent_entity_calendar.start_date - timezone.timedelta(days=5),
            end_date=cls.parent_entity_calendar.end_date - timezone.timedelta(days=2)
        )

    def test_when_entity_version_has_entity_calendar(self):
        child_entity_dates = find_summary_course_submission_dates_for_entity_version(self.child_entity_version_bis)
        self.assertEqual(child_entity_dates, {'start_date': self.child_entity_calendar_bis.start_date.date(),
                                              'end_date': self.child_entity_calendar_bis.end_date.date()})

    def test_when_parent_has_entity_calendar_instance(self):
        child_entity_dates = find_summary_course_submission_dates_for_entity_version(self.child_entity_version)
        self.assertEqual(child_entity_dates, {'start_date': self.parent_entity_calendar.start_date.date(),
                                              'end_date': self.parent_entity_calendar.end_date.date()})

    def test_when_no_parent_has_entity_calendar_instance(self):
        default_entity_dates = find_summary_course_submission_dates_for_entity_version(
            self.entity_version_without_entity_calendar
        )
        self.assertEqual(default_entity_dates, {'start_date': self.academic_calendar.start_date,
                                                'end_date': self.academic_calendar.end_date})


class TestUserCanEditEntityCalendarEducationalInformation(TestCase):
    @classmethod
    def setUpTestData(cls):
        person_entity = PersonEntityFactory()
        cls.user = person_entity.person.user
        cls.entity = person_entity.entity
        FacultyManagerGroupFactory()
        cls.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))

        cls.user_not_faculty_manager = PersonEntityFactory(entity=cls.entity).person.user

        cls.user_with_no_person = UserFactory()

        cls.entity_not_linked_to = EntityFactory()

    def test_when_user_not_linked_to_person(self):
        with self.assertRaises(Http404):
            can_user_edit_educational_information_submission_dates_for_entity(self.user_with_no_person, self.entity)

    def test_when_not_faculty_manager(self):
        can_user_edit = can_user_edit_educational_information_submission_dates_for_entity(self.user_not_faculty_manager,
                                                                                          self.entity)
        self.assertFalse(can_user_edit)

    def test_when_faculty_manager_but_not_linked_to_entity(self):
        can_user_edit = can_user_edit_educational_information_submission_dates_for_entity(self.user,
                                                                                          self.entity_not_linked_to)
        self.assertFalse(can_user_edit)

    def test_when_faculty_manager_and_linked_to_entity(self):
        can_user_edit = can_user_edit_educational_information_submission_dates_for_entity(self.user,
                                                                                          self.entity)
        self.assertTrue(can_user_edit)
