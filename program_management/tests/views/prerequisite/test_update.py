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
import json

import mock
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, EducationGroupYearBachelorFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory, LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory


class TestUpdateLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.education_group_year_parent = EducationGroupYearBachelorFactory(academic_year=cls.academic_year)
        cls.learning_unit_year_child = LearningUnitYearFakerFactory(
            learning_container_year__academic_year=cls.academic_year
        )

        GroupElementYearFactory(
            parent=cls.education_group_year_parent,
            child_leaf=cls.learning_unit_year_child,
            child_branch=None
        )
        cls.person = CentralManagerFactory(entity=cls.education_group_year_parent.management_entity).person

        cls.url = reverse("learning_unit_prerequisite_update",
                          args=[cls.education_group_year_parent.id, cls.learning_unit_year_child.id])

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_not_found_when_learning_unit_not_contained_in_training(self):
        other_education_group_year = TrainingFactory(
            academic_year=self.academic_year,
            management_entity=self.education_group_year_parent.management_entity
        )
        url = reverse("learning_unit_prerequisite_update",
                      args=[other_education_group_year.id, self.learning_unit_year_child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_permission_denied_when_context_not_a_formation(self):
        group_parent = GroupFactory(academic_year=self.academic_year)
        PersonEntityFactory(person=self.person, entity=group_parent.management_entity)
        url = reverse("learning_unit_prerequisite_update",
                      args=[group_parent.id, self.learning_unit_year_child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/tab_prerequisite_update.html")

    def test_context(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertEqual(
            context['root'],
            self.education_group_year_parent
        )

        tree = json.loads(context['tree'])
        self.assertTrue(tree)
        self.assertEqual(
            tree['text'],
            self.education_group_year_parent.verbose
        )

    @mock.patch("program_management.ddd.repositories._persist_prerequisite.persist")
    def test_post_data_simple_prerequisite(self, mock_persist):
        luy_1 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parent, child_leaf=luy_1)

        form_data = {
            "prerequisite_string": "LSINF1111"
        }
        response = self.client.post(self.url, data=form_data)

        redirect_url = reverse(
            "learning_unit_prerequisite",
            args=[self.education_group_year_parent.id, self.learning_unit_year_child.id]
        )
        self.assertRedirects(response, redirect_url)

        self.assertTrue(mock_persist.called)
