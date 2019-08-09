##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.models import Group
from django.test import TestCase

from base.business.learning_unit_proposal import compute_proposal_state
from base.models.enums import proposal_state
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.tests.factories.group import CentralManagerGroupFactory, FacultyManagerGroupFactory
from base.tests.factories.person import PersonFactory


def create_person_in_group(group_name):
    a_person = PersonFactory()
    a_person.user.groups.add(Group.objects.get(name=group_name))
    return a_person


class TestComputeProposalState(TestCase):
    def test_when_person_is_faculty_manager(self):
        FacultyManagerGroupFactory()
        faculty_manager = create_person_in_group(FACULTY_MANAGER_GROUP)

        expected_state = proposal_state.ProposalState.FACULTY.name
        actual_state = compute_proposal_state(faculty_manager)
        self.assertEqual(expected_state, actual_state)

    def test_when_person_is_central_manager(self):
        CentralManagerGroupFactory()
        central_manager = create_person_in_group(CENTRAL_MANAGER_GROUP)

        expected_state = proposal_state.ProposalState.CENTRAL.name
        actual_state = compute_proposal_state(central_manager)
        self.assertEqual(expected_state, actual_state)

    def test_when_person_is_nor_a_faculty_manager_nor_a_central_manager(self):
        person = PersonFactory()

        expected_state = proposal_state.ProposalState.FACULTY.name
        actual_state = compute_proposal_state(person)
        self.assertEqual(expected_state, actual_state)
