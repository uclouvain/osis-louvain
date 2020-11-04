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
from unittest import skip

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory
from base.tests.factories.person import PersonWithPermissionsFactory

from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory


class TestLearningUnitFormationsTab(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.learning_container_year = LearningContainerYearFactory(
            container_type=LearningContainerYearType.COURSE.name,
            academic_year=cls.academic_year
        )
        cls.person = PersonWithPermissionsFactory('can_access_learningunit')
        cls.learning_unit_year = LearningUnitYearFullFactory(
            learning_container_year=cls.learning_container_year,
            academic_year=cls.academic_year
        )
        cls.elem_learning_unit_year = ElementFactory(learning_unit_year=cls.learning_unit_year)

        cls.group_year = GroupYearFactory(
            academic_year=cls.academic_year
        )

        cls.elem_group_year = ElementFactory(group_year=cls.group_year)
        cls.group_element_year = GroupElementYearFactory(
            parent_element=cls.elem_group_year,
            child_element=cls.elem_learning_unit_year
        )

        cls.education_group_year_formation_parent = TrainingFactory(
            academic_year=cls.academic_year
        )
        cls.education_group_version_formation_parent = StandardEducationGroupVersionFactory(
            offer=cls.education_group_year_formation_parent,
            root_group__academic_year=cls.academic_year,
            root_group__education_group_type=cls.education_group_year_formation_parent.education_group_type,
            root_group__partial_acronym=cls.education_group_year_formation_parent.partial_acronym
        )
        cls.elem_education_group_version_formation_parent = ElementFactory(
            group_year=cls.education_group_version_formation_parent.root_group)
        GroupElementYearFactory(
            parent_element=cls.elem_education_group_version_formation_parent,
            child_element=cls.elem_group_year
        )

        cls.education_group_year_formation_great_parent_1 = TrainingFactory(
            academic_year=cls.academic_year
        )
        cls.education_group_version_formation_great_parent_1 = StandardEducationGroupVersionFactory(
            offer=cls.education_group_year_formation_great_parent_1,
            root_group__academic_year=cls.academic_year,
            root_group__education_group_type=cls.education_group_year_formation_great_parent_1.education_group_type,
            root_group__partial_acronym=cls.education_group_year_formation_great_parent_1.partial_acronym
        )
        cls.elem_education_group_version_formation_great_parent_1 = ElementFactory(
            group_year=cls.education_group_version_formation_great_parent_1.root_group
        )
        GroupElementYearFactory(
            parent_element=cls.elem_education_group_version_formation_great_parent_1,
            child_element=cls.elem_group_year
        )
        cls.education_group_year_formation_great_parent_2 = TrainingFactory(
            academic_year=cls.academic_year
        )
        cls.education_group_version_formation_great_parent_2 = StandardEducationGroupVersionFactory(
            offer=cls.education_group_year_formation_great_parent_2,
            root_group__academic_year=cls.academic_year,
            root_group__education_group_type=cls.education_group_year_formation_great_parent_2.education_group_type,
            root_group__partial_acronym=cls.education_group_year_formation_great_parent_2.partial_acronym
        )
        cls.elem_education_group_version_formation_great_parent_2 = ElementFactory(
            group_year=cls.education_group_version_formation_great_parent_2.root_group
        )
        GroupElementYearFactory(
            parent_element=cls.elem_education_group_version_formation_great_parent_2,
            child_element=cls.elem_group_year
        )

    def setUp(self):
        self.client.force_login(self.person.user)
        self.url = reverse("learning_unit_formations", args=[self.learning_unit_year.id])

    def test_formations_tab(self):
        response = self.client.get(self.url)
        with self.subTest('1'):
            self.assertCountEqual(response.context['formations_by_educ_group_year'].get(self.elem_learning_unit_year.pk),
                                  [self.elem_group_year])
        with self.subTest('2'):
            self.assertCountEqual(response.context['formations_by_educ_group_year'].get(self.elem_group_year.pk),
                                  [self.elem_education_group_version_formation_parent,
                                   self.elem_education_group_version_formation_great_parent_1,
                                   self.elem_education_group_version_formation_great_parent_2]
                                  )

        with self.subTest('3'):
            self.assertCountEqual(
                list(response.context['group_elements_years']),
                [self.group_element_year]
            )

    def test_tab_active_url(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue("tab_active" in response.context)
        self.assertEqual(response.context["tab_active"], 'learning_unit_formations')

        url_tab_active = reverse(response.context["tab_active"], args=[self.learning_unit_year.id])
        response = self.client.get(url_tab_active)
        self.assertEqual(response.status_code, HttpResponse.status_code)
