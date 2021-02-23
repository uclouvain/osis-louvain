##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import mock
from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory, \
    MiniTrainingEducationGroupTypeFactory
from base.tests.factories.user import UserFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory


class TestGetCreateProgramTreeSpecificVersion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.current_year = cls.current_academic_year.year
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year, 10)

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT,
            data_year=cls.current_academic_year
        )
        cls.factulty_manager = FacultyManagerFactory(entity=cls.central_manager.entity)

        cls.training_type = TrainingEducationGroupTypeFactory()
        cls.training_version = StandardEducationGroupVersionFactory(
            offer__acronym="DROI2M",
            offer__partial_acronym="LDROI200M",
            offer__academic_year=cls.current_academic_year,
            offer__education_group_type=cls.training_type,
            offer__management_entity=cls.central_manager.entity,

            root_group__acronym="DROI2M",
            root_group__partial_acronym="LDROI200M",
            root_group__academic_year=cls.current_academic_year,
            root_group__education_group_type=cls.training_type,
            root_group__management_entity=cls.central_manager.entity
        )
        ElementFactory(group_year=cls.training_version.root_group)
        cls.create_training_version_url = reverse(
            "create_education_group_specific_version",
            kwargs={
                "year": cls.training_version.root_group.academic_year.year,
                "code": cls.training_version.root_group.partial_acronym
            }
        )

        cls.mini_training_type = MiniTrainingEducationGroupTypeFactory()
        cls.mini_training_version = StandardEducationGroupVersionFactory(
            offer__acronym="OPTDROI2M/AR",
            offer__partial_acronym="LDROP221O",
            offer__academic_year=cls.current_academic_year,
            offer__education_group_type=cls.mini_training_type,
            offer__management_entity=cls.central_manager.entity,

            root_group__acronym="OPTDROI2M/AR",
            root_group__partial_acronym="LDROP221O",
            root_group__academic_year=cls.current_academic_year,
            root_group__education_group_type=cls.mini_training_type,
            root_group__management_entity=cls.central_manager.entity
        )
        ElementFactory(group_year=cls.mini_training_version.root_group)
        cls.create_mini_training_version_url = reverse(
            "create_education_group_specific_version",
            kwargs={
                "year": cls.mini_training_version.root_group.academic_year.year,
                "code": cls.mini_training_version.root_group.partial_acronym
            }
        )

    def test_case_user_not_logged(self):
        response = self.client.get(self.create_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_case_user_unauthorized(self):
        unauthorized_user = UserFactory()

        self.client.force_login(unauthorized_user)
        response = self.client.get(self.create_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_user_as_central_manager_for_create_training_version(self):
        self.client.force_login(self.central_manager.person.user)

        response = self.client.get(self.create_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_specific_version_inner.html")

    def test_case_user_as_central_manager_for_create_mini_training_version(self):
        self.client.force_login(self.central_manager.person.user)

        response = self.client.get(self.create_mini_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_specific_version_inner.html")

    def test_case_user_as_faculty_manager_for_create_training_version(self):
        self.client.force_login(self.factulty_manager.person.user)
        response = self.client.get(self.create_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch('education_group.calendar.education_group_preparation_calendar.'
                'EducationGroupPreparationCalendar.is_target_year_authorized', return_value=True)
    def test_case_user_as_faculty_manager_for_create_mini_training_version(self, mock_perms):
        self.client.force_login(self.factulty_manager.person.user)
        response = self.client.get(self.create_mini_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_specific_version_inner.html")


class TestGetCreateProgramTreeTransitionVersion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.current_year = cls.current_academic_year.year
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year, 10)

        cls.central_manager = CentralManagerFactory()
        OpenAcademicCalendarFactory(
            reference=academic_calendar_type.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT,
            data_year=cls.current_academic_year
        )
        cls.factulty_manager = FacultyManagerFactory(entity=cls.central_manager.entity)

        cls.training_type = TrainingEducationGroupTypeFactory()
        cls.training_version = StandardEducationGroupVersionFactory(
            offer__acronym="DROI2M",
            offer__partial_acronym="LDROI200M",
            offer__academic_year=cls.current_academic_year,
            offer__education_group_type=cls.training_type,
            offer__management_entity=cls.central_manager.entity,

            root_group__acronym="DROI2M",
            root_group__partial_acronym="LDROI200M",
            root_group__academic_year=cls.current_academic_year,
            root_group__education_group_type=cls.training_type,
            root_group__management_entity=cls.central_manager.entity
        )
        ElementFactory(group_year=cls.training_version.root_group)
        cls.create_training_version_url = reverse(
            "create_education_group_transition_version",
            kwargs={
                "year": cls.training_version.root_group.academic_year.year,
                "code": cls.training_version.root_group.partial_acronym
            }
        )

        cls.mini_training_type = MiniTrainingEducationGroupTypeFactory()
        cls.mini_training_version = StandardEducationGroupVersionFactory(
            offer__acronym="OPTDROI2M/AR",
            offer__partial_acronym="LDROP221O",
            offer__academic_year=cls.current_academic_year,
            offer__education_group_type=cls.mini_training_type,
            offer__management_entity=cls.central_manager.entity,

            root_group__acronym="OPTDROI2M/AR",
            root_group__partial_acronym="LDROP221O",
            root_group__academic_year=cls.current_academic_year,
            root_group__education_group_type=cls.mini_training_type,
            root_group__management_entity=cls.central_manager.entity
        )
        ElementFactory(group_year=cls.mini_training_version.root_group)
        cls.create_mini_training_version_url = reverse(
            "create_education_group_transition_version",
            kwargs={
                "year": cls.mini_training_version.root_group.academic_year.year,
                "code": cls.mini_training_version.root_group.partial_acronym
            }
        )

    def test_case_user_not_logged(self):
        response = self.client.get(self.create_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_case_user_unauthorized(self):
        unauthorized_user = UserFactory()

        self.client.force_login(unauthorized_user)
        response = self.client.get(self.create_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_case_user_as_central_manager_for_create_training_version(self):
        self.client.force_login(self.central_manager.person.user)

        response = self.client.get(self.create_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_transition_version_inner.html")

    def test_case_user_as_central_manager_for_create_mini_training_version(self):
        self.client.force_login(self.central_manager.person.user)

        response = self.client.get(self.create_mini_training_version_url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_transition_version_inner.html")

    def test_case_user_as_faculty_manager_for_create_training_version(self):
        self.client.force_login(self.factulty_manager.person.user)
        response = self.client.get(self.create_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    @mock.patch('education_group.calendar.education_group_preparation_calendar.'
                'EducationGroupPreparationCalendar.is_target_year_authorized', return_value=True)
    def test_case_user_as_faculty_manager_for_create_mini_training_version(self, mock_perms):
        self.client.force_login(self.factulty_manager.person.user)
        response = self.client.get(self.create_mini_training_version_url, data={}, follow=True)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_transition_version_inner.html")
