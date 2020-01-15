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

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory
from base.tests.factories.person import PersonWithPermissionsFactory


class TestLearningUnitFormationsTab(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(current=True)
        self.learning_container_year = LearningContainerYearFactory(
            container_type=LearningContainerYearType.COURSE.name,
            academic_year=self.academic_year
        )
        self.person = PersonWithPermissionsFactory('can_access_learningunit')
        self.learning_unit_year = LearningUnitYearFullFactory(
            learning_container_year=self.learning_container_year,
            academic_year=self.academic_year
        )

        self.education_group_year = EducationGroupYearFactory(
            academic_year=self.academic_year
        )
        self.group_element_year = GroupElementYearFactory(
            parent=self.education_group_year,
            child_branch=None,
            child_leaf=self.learning_unit_year
        )

        self.education_group_year_formation_parent = EducationGroupYearFactory(
            academic_year=self.academic_year
        )
        GroupElementYearFactory(
            parent=self.education_group_year_formation_parent,
            child_branch=self.education_group_year
        )

        self.education_group_year_formation_great_parent_1 = EducationGroupYearFactory(
            academic_year=self.academic_year
        )
        GroupElementYearFactory(
            parent=self.education_group_year_formation_great_parent_1,
            child_branch=self.education_group_year_formation_parent
        )
        self.education_group_year_formation_great_parent_2 = EducationGroupYearFactory(
            academic_year=self.academic_year
        )
        GroupElementYearFactory(
            parent=self.education_group_year_formation_great_parent_2,
            child_branch=self.education_group_year_formation_parent
        )

        self.client.force_login(self.person.user)
        self.url = reverse("learning_unit_formations", args=[self.learning_unit_year.id])

    def test_formations_tab(self):

        response = self.client.get(self.url)
        self.assertCountEqual(response.context['formations_by_educ_group_year'].get(self.education_group_year.pk),
                              [self.education_group_year_formation_parent])
        self.assertCountEqual(response.context['formations_by_educ_group_year'].
                              get(self.education_group_year_formation_parent.pk),
                              [self.education_group_year_formation_great_parent_1,
                               self.education_group_year_formation_great_parent_2]
                              )

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
