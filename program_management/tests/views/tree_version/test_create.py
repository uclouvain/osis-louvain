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

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import CentralManagerForUEFactory, PersonFactory, FacultyManagerForUEFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory
from program_management.views.tree_version.create import CreateProgramTreeVersionType


class TestCreateProgramTreeVersion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.current_year = cls.current_academic_year.year
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year, 10)
        cls.type = TrainingEducationGroupTypeFactory()

        cls.group_year = GroupYearFactory(
            academic_year=cls.current_academic_year,
            partial_acronym="LDROI200M"
        )

        cls.education_group_year = EducationGroupYearFactory(
            academic_year=cls.current_academic_year,
            education_group_type=cls.type,
            acronym=cls.group_year.acronym
        )

        cls.education_group_version = EducationGroupVersionFactory(
            offer=cls.education_group_year,
            root_group=cls.group_year,
            version_name=""
        )

        cls.element = ElementFactory(group_year=cls.group_year)

        cls.central_manager = CentralManagerForUEFactory("view_educationgroup")
        cls.factulty_manager = FacultyManagerForUEFactory("view_educationgroup")
        cls.simple_user = PersonFactory()

        cls.valid_data = {
            "version_name": "CMS",
            "title": "Titre",
            "title_english": "Title",
            "end_year": cls.current_year,
            "save_type": CreateProgramTreeVersionType.NEW_VERSION.value
        }
        cls.url = reverse(
            "create_education_group_version",
            kwargs={"year": cls.group_year.academic_year.year, "code": cls.group_year.partial_acronym}
        )

    def test_get_init_form_create_program_tree_version_with_disconected_user(self):
        response = self.client.get(self.url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_get_init_form_create_program_tree_version_for_central_manager(self):
        self.client.force_login(self.central_manager.user)
        response = self.client.get(self.url, data={}, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "tree_version/create_specific_version_inner.html")

    def test_get_init_form_create_program_tree_version_for_faculty_manager(self):
        self.client.force_login(self.factulty_manager.user)
        response = self.client.get(self.url, data={}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_get_init_form_create_program_tree_version_for_simple_user(self):
        self.client.force_login(self.simple_user.user)
        response = self.client.get(self.url, data={}, follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_get_context_form(self):
        self.client.force_login(self.central_manager.user)
        response = self.client.get(self.url, data={}, follow=True)
        self.assertEqual(len(response.context['form'].fields['end_year'].choices), 8)
        self.assertEqual(response.context['form'].fields['end_year'].choices[0][0], None)
        self.assertEqual(response.context['form'].fields['end_year'].choices[7][0], self.current_year + 6)
        self.assertEqual(response.context['form'].fields['end_year'].initial, None)
