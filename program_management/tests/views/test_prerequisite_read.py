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
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestLearningUnitPrerequisiteTraining(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.offer = TrainingFactory(academic_year=cls.academic_year)
        cls.root_group = GroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type=cls.offer.education_group_type
        )
        cls.root_element = ElementGroupYearFactory(group_year=cls.root_group)
        cls.education_group_version = EducationGroupVersionFactory(offer=cls.offer, root_group=cls.root_group)

        cls.element_learning_unit_year = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year=cls.academic_year,
            learning_unit_year__learning_container_year__academic_year=cls.academic_year,
        )
        GroupElementYearChildLeafFactory(parent_element=cls.root_element, child_element=cls.element_learning_unit_year)

        cls.prerequisite = PrerequisiteFactory(
            learning_unit_year=cls.element_learning_unit_year.learning_unit_year,
            education_group_version=cls.education_group_version
        )

        cls.person = PersonWithPermissionsFactory("view_educationgroup")
        cls.url = reverse(
            "learning_unit_prerequisite",
            kwargs={
                'root_element_id': cls.root_element.pk,
                'child_element_id': cls.element_learning_unit_year.pk
            }
        )

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/tab_prerequisite_training.html")


class TestLearningUnitPrerequisiteGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.offer = TrainingFactory(academic_year=cls.academic_year)
        cls.root_group = GroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type__category=Categories.GROUP.name,
            education_group_type__name=GroupType.COMMON_CORE.name,
        )
        cls.root_element = ElementGroupYearFactory(group_year=cls.root_group)
        cls.element_learning_unit_year = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year=cls.academic_year,
            learning_unit_year__learning_container_year__academic_year=cls.academic_year,
        )
        GroupElementYearChildLeafFactory(parent_element=cls.root_element, child_element=cls.element_learning_unit_year)
        cls.education_group_version = EducationGroupVersionFactory(offer=cls.offer, root_group=cls.root_group)

        cls.person = PersonWithPermissionsFactory("view_educationgroup")
        cls.url = reverse(
            "learning_unit_prerequisite",
            kwargs={
                'root_element_id': cls.root_element.pk,
                'child_element_id': cls.element_learning_unit_year.pk
            }
        )

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/tab_prerequisite_group.html")
