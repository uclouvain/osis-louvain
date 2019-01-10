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

from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.education_group_types import GroupType
from base.tests.factories.academic_calendar import CloseAcademicCalendarFactory, \
    OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory
from base.tests.factories.person import PersonFactory, CentralManagerFactory, FacultyManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.views.education_groups.group_element_year.perms import can_create_group_element_year


class TestCanCreateGroupElementYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_acy, cls.previous_acy = AcademicYearFactory.produce_in_past(quantity=2)
        cls.training_egy = TrainingFactory(academic_year=cls.current_acy)

    def test_raise_permission_denied_when_user_not_linked_to_entity(self):
        person = PersonFactory()
        with self.assertRaises(PermissionDenied):
            can_create_group_element_year(person.user, self.training_egy)

    def test_return_true_if_is_central_manager(self):
        person_entity = PersonEntityFactory(entity=self.training_egy.management_entity,
                                            person=CentralManagerFactory())

        self.assertTrue(can_create_group_element_year(person_entity.person.user, self.training_egy))

    def test_raise_permission_denied_if_person_is_faculty_manager_and_period_closed(self):
        CloseAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.previous_acy)
        person_entity = PersonEntityFactory(entity=self.training_egy.management_entity,
                                            person=FacultyManagerFactory())

        with self.assertRaises(PermissionDenied):
            can_create_group_element_year(person_entity.person.user, self.training_egy)

    def test_raise_permission_denied_when_minor_or_major_list_choice_and_person_is_faculty_manager(self):
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.previous_acy)
        egys = [
            GroupFactory(education_group_type__name=GroupType.MINOR_LIST_CHOICE.name, academic_year=self.current_acy),
            GroupFactory(education_group_type__name=GroupType.MAJOR_LIST_CHOICE.name, academic_year=self.current_acy)
        ]
        person_entity = PersonEntityFactory(entity=self.training_egy.management_entity,
                                            person=FacultyManagerFactory())

        for egy in egys:
            with self.subTest(type=egy.education_group_type):
                with self.assertRaises(PermissionDenied):
                    can_create_group_element_year(person_entity.person.user, egy)
