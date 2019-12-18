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

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.education_group_types import GroupType, MiniTrainingType
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, PROGRAM_MANAGER_GROUP
from base.tests.business.test_perms import create_person_with_permission_and_group
from base.tests.factories.academic_calendar import CloseAcademicCalendarFactory, \
    OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory, FacultyManagerFactory, PersonWithPermissionsFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from program_management.views.perms import can_update_group_element_year, \
    can_detach_group_element_year


class TestCanUpdateGroupElementYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_acy, cls.previous_acy = AcademicYearFactory.produce_in_past(from_year=2019, quantity=2)
        cls.group_element_year = GroupElementYearFactory(
            parent=TrainingFactory(academic_year=cls.current_acy),
            child_branch=MiniTrainingFactory(
                academic_year=cls.current_acy,
                education_group_type__name=MiniTrainingType.DEEPENING.name
            ),
        )
        cls.faculty_manager = FacultyManagerFactory()
        cls.faculty_manager.user.user_permissions.add(Permission.objects.get(codename="change_educationgroup"))
        PersonEntityFactory(
            entity=cls.group_element_year.parent.management_entity,
            person=cls.faculty_manager
        )

    def test_raise_permission_denied_when_user_not_linked_to_entity(self):
        person = PersonFactory()
        with self.assertRaises(PermissionDenied):
            can_update_group_element_year(person.user, self.group_element_year)

    def test_return_true_if_is_central_manager(self):
        central_manager = create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP, 'change_educationgroup')
        person_entity = PersonEntityFactory(entity=self.group_element_year.parent.management_entity,
                                            person=central_manager)

        self.assertTrue(can_update_group_element_year(person_entity.person.user, self.group_element_year))

    def test_return_true_if_child_is_learning_unit_and_user_is_central_manager(self):
        central_manager = create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP, 'change_educationgroup')
        GroupElementYearChildLeafFactory(parent=self.group_element_year.parent)
        person_entity = PersonEntityFactory(entity=self.group_element_year.parent.management_entity,
                                            person=central_manager)

        self.assertTrue(can_update_group_element_year(person_entity.person.user, self.group_element_year))

    def test_true_if_person_is_faculty_manager_and_period_open(self):
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.current_acy,
                                    data_year=self.current_acy)

        self.assertTrue(can_update_group_element_year(self.faculty_manager.user, self.group_element_year))

    def test_raise_permission_denied_if_person_is_faculty_manager_and_period_closed(self):
        CloseAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.current_acy,
                                     data_year=self.current_acy)

        with self.assertRaises(PermissionDenied):
            can_update_group_element_year(self.faculty_manager.user, self.group_element_year)

    def test_raise_permission_denied_if_person_is_program_manager(self):
        program_manager = PersonWithPermissionsFactory(groups=(PROGRAM_MANAGER_GROUP, ))
        with self.assertRaises(PermissionDenied):
            can_update_group_element_year(program_manager.user, self.group_element_year)

    def test_raise_permission_denied_when_minor_or_major_list_choice_and_person_is_faculty_manager(self):
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.current_acy)
        egys = [
            GroupFactory(education_group_type__name=GroupType.MINOR_LIST_CHOICE.name, academic_year=self.current_acy),
            GroupFactory(education_group_type__name=GroupType.MAJOR_LIST_CHOICE.name, academic_year=self.current_acy)
        ]

        for egy in egys:
            with self.subTest(type=egy.education_group_type):
                with self.assertRaises(PermissionDenied):
                    group_element_year = GroupElementYearFactory(parent=self.group_element_year.parent,
                                                                 child_branch=egy)
                    can_update_group_element_year(self.faculty_manager.user, group_element_year)

    def test_detach(self):
        calendar = OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.current_acy,
                                               data_year=self.current_acy)
        group_element_year = GroupElementYearFactory(parent=self.group_element_year.parent)

        can_detach_group_element_year(self.faculty_manager.user, group_element_year)

        calendar.delete()

        with self.assertRaises(PermissionDenied):
            can_detach_group_element_year(self.faculty_manager.user, group_element_year)
