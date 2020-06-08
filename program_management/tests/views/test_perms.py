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
from mock import patch

from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.education_group_types import GroupType, MiniTrainingType
from base.models.enums.groups import PROGRAM_MANAGER_GROUP
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory


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
        cls.faculty_manager = FacultyManagerFactory(entity=cls.group_element_year.parent.management_entity)
        cls.permission_required = 'base.change_link_data'

    def test_return_false_when_user_not_linked_to_entity(self):
        person = PersonFactory()
        self.assertFalse(person.user.has_perm(self.permission_required, self.group_element_year.parent))

    def test_return_true_if_is_central_manager(self):
        central_manager = CentralManagerFactory(entity=self.group_element_year.parent.management_entity).person
        self.assertTrue(central_manager.user.has_perm(self.permission_required, self.group_element_year.parent))

    def test_return_true_if_child_is_learning_unit_and_user_is_central_manager(self):
        GroupElementYearChildLeafFactory(parent=self.group_element_year.parent)
        central_manager = CentralManagerFactory(entity=self.group_element_year.parent.management_entity)

        self.assertTrue(central_manager.person.user.has_perm(self.permission_required, self.group_element_year.parent))

    def test_true_if_person_is_faculty_manager_and_period_open(self):
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=self.current_acy,
                                    data_year=self.current_acy)

        self.assertTrue(
            self.faculty_manager.person.user.has_perm(self.permission_required, self.group_element_year.parent)
        )

    @patch('base.business.event_perms.EventPerm.is_open', return_value=False)
    def test_raise_permission_denied_if_person_is_faculty_manager_and_period_closed(self, mock_period_open):
        self.assertFalse(
            self.faculty_manager.person.user.has_perm(self.permission_required, self.group_element_year.parent)
        )

    def test_raise_permission_denied_if_person_is_program_manager(self):
        program_manager = PersonWithPermissionsFactory(groups=(PROGRAM_MANAGER_GROUP, ))
        self.assertFalse(program_manager.user.has_perm(self.permission_required, self.group_element_year.parent))

    def test_true_if_person_has_both_roles(self):
        person_with_both_roles = PersonWithPermissionsFactory(
            'change_link_data',
            groups=(PROGRAM_MANAGER_GROUP,)
        )
        CentralManagerFactory(person=person_with_both_roles, entity=self.group_element_year.parent.management_entity)

        self.assertTrue(person_with_both_roles.user.has_perm(self.permission_required, self.group_element_year.parent))

    @patch('base.business.event_perms.EventPerm.is_open', return_value=True)
    def test_raise_permission_denied_when_minor_or_major_list_choice_and_person_is_faculty_manager(self, mock_period):
        egys = [
            GroupFactory(education_group_type__name=GroupType.MINOR_LIST_CHOICE.name, academic_year=self.current_acy),
            GroupFactory(education_group_type__name=GroupType.MAJOR_LIST_CHOICE.name, academic_year=self.current_acy)
        ]
        for egy in egys:
            with self.subTest(type=egy.education_group_type):
                group_element_year = GroupElementYearFactory(
                    parent=self.group_element_year.parent,
                    child_branch=egy
                )
                self.assertFalse(
                    self.faculty_manager.person.user.has_perm(self.permission_required, group_element_year.child_branch)
                )
