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
import mock
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import GroupType, TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearBachelorFactory, \
    EducationGroupYearMasterFactory
from base.tests.factories.group_element_year import GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory
from education_group.models.group_year import GroupYear
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestUpdateLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)

        offer = EducationGroupYearBachelorFactory(academic_year=cls.academic_year)
        root_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type=offer.education_group_type,
            group_year__management_entity=offer.management_entity
        )
        cls.educucation_group_version = EducationGroupVersionFactory(offer=offer, root_group=root_element.group_year)

        cls.element_learning_unit_year = ElementLearningUnitYearFactory(
            learning_unit_year__learning_container_year__academic_year=cls.academic_year
        )

        GroupElementYearChildLeafFactory(parent_element=root_element, child_element=cls.element_learning_unit_year)
        cls.central_manager = CentralManagerFactory(entity=offer.management_entity)

        cls.url = reverse(
            "learning_unit_prerequisite_update",
            kwargs={
                'root_element_id': root_element.pk,
                'child_element_id': cls.element_learning_unit_year.pk
            }
        )

    def setUp(self):
        self.client.force_login(self.central_manager.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_not_found_when_learning_unit_not_contained_in_training(self):
        other_education_group_year = EducationGroupYearMasterFactory(academic_year=self.academic_year)
        root_element = ElementGroupYearFactory(
            group_year__academic_year=other_education_group_year.academic_year,
            group_year__education_group_type=other_education_group_year.education_group_type,
            group_year__management_entity=self.central_manager.entity
        )
        EducationGroupVersionFactory(offer=other_education_group_year, root_group=root_element.group_year)

        url = reverse(
            "learning_unit_prerequisite_update",
            kwargs={
                'root_element_id': root_element.id,
                'child_element_id': self.element_learning_unit_year.pk
            }
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_permission_denied_when_root_element_not_a_formation(self):
        group_element = ElementGroupYearFactory(
            group_year__academic_year=self.academic_year,
            group_year__education_group_type__name=GroupType.COMMON_CORE.name,
            group_year__management_entity=self.central_manager.entity
        )
        GroupElementYearChildLeafFactory(parent_element=group_element, child_element=self.element_learning_unit_year)

        url = reverse(
            "learning_unit_prerequisite_update",
            kwargs={
                'root_element_id': group_element.pk,
                'child_element_id': self.element_learning_unit_year.pk
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/tab_prerequisite_update.html")

    def test_assert_keys_context(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertIsInstance(context['root'], GroupYear)  # TODO : Should be NodeGroupYear instead
        self.assertTrue('tree' in context)
        self.assertTrue(context['show_prerequisites'])

    @mock.patch("program_management.ddd.repositories._persist_prerequisite.persist")
    def test_post_data_simple_prerequisite(self, mock_persist):
        luy_element = ElementLearningUnitYearFactory(
            learning_unit_year__acronym='LSINF1111',
            learning_unit_year__academic_year=self.academic_year
        )
        GroupElementYearChildLeafFactory(
            parent_element=self.educucation_group_version.root_group.element,
            child_element=luy_element
        )

        form_data = {
            "prerequisite_string": "LSINF1111"
        }
        response = self.client.post(self.url, data=form_data)

        redirect_url = reverse(
            "learning_unit_prerequisite",
            kwargs={
                'root_element_id': self.educucation_group_version.root_group.element.pk,
                'child_element_id': self.element_learning_unit_year.pk
            }
        )
        self.assertRedirects(response, redirect_url)
        self.assertTrue(mock_persist.called)
