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

from attribution.models.enums.function import COORDINATOR
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_subtypes import PARTIM
from base.tests.factories.academic_calendar import generate_learning_unit_edition_calendars
from base.tests.factories.learning_component_year import LecturingLearningComponentYearFactory, \
    PracticalLearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory
from learning_unit.tests.factories.faculty_manager import FacultyManagerFactory


class TestEditAttributionGet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_container_year = LearningContainerYearFactory(
            container_type=LearningContainerYearType.MASTER_THESIS.name
        )
        cls.learning_unit_year = LearningUnitYearFullFactory(
            learning_container_year=cls.learning_container_year
        )
        cls.lecturing_component = LecturingLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year)
        cls.practical_component = PracticalLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year)
        cls.attribution = AttributionNewFactory(
            learning_container_year=cls.learning_container_year,
        )
        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.lecturing_component
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.practical_component
        )
        cls.person = FacultyManagerFactory(entity=cls.learning_container_year.requirement_entity).person
        generate_learning_unit_edition_calendars([cls.learning_unit_year.academic_year])

    def setUp(self):
        self.client.force_login(self.person.user)
        self.url = reverse("update_attribution", args=[self.learning_unit_year.id, self.attribution.id])

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_template_used_with_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "attribution/learning_unit/attribution_inner.html")


class TestEditAttributionPost(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_container_year = LearningContainerYearFactory(
            container_type=LearningContainerYearType.MASTER_THESIS.name
        )
        cls.learning_unit_year = LearningUnitYearFullFactory(
            learning_container_year=cls.learning_container_year
        )
        cls.lecturing_component = LecturingLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year)
        cls.practical_component = PracticalLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year)
        cls.attribution = AttributionNewFactory(
            learning_container_year=cls.learning_container_year,
        )
        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.lecturing_component
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.practical_component
        )
        cls.person = FacultyManagerFactory(entity=cls.learning_container_year.requirement_entity).person
        generate_learning_unit_edition_calendars([cls.learning_unit_year.academic_year])

    def setUp(self):
        self.client.force_login(self.person.user)
        self.url = reverse("update_attribution", args=[self.learning_unit_year.id, self.attribution.id])

    def test_post(self):
        data = {
            'attribution_form-function': COORDINATOR,
            'lecturing_form-allocation_charge': 50,
            'practical_form-allocation_charge': 10
        }
        response = self.client.post(self.url, data=data)

        self.attribution.refresh_from_db()
        self.charge_lecturing.refresh_from_db()
        self.charge_practical.refresh_from_db()
        self.assertEqual(self.attribution.function, COORDINATOR)
        self.assertEqual(self.charge_lecturing.allocation_charge, 50)
        self.assertEqual(self.charge_practical.allocation_charge, 10)

        self.assertRedirects(response,
                             reverse("learning_unit_attributions", args=[self.learning_unit_year.id]))

    def test_post_partim(self):
        self.learning_unit_year.subtype = PARTIM
        self.learning_unit_year.save()
        data = {
            'attribution_form-function': COORDINATOR,
            'lecturing_form-allocation_charge': 50,
            'practical_form-allocation_charge': 10
        }
        response = self.client.post(self.url, data=data)

        self.attribution.refresh_from_db()
        self.charge_lecturing.refresh_from_db()
        self.charge_practical.refresh_from_db()
        self.assertEqual(self.charge_lecturing.allocation_charge, 50)
        self.assertEqual(self.charge_practical.allocation_charge, 10)

        self.assertRedirects(response,
                             reverse("learning_unit_attributions", args=[self.learning_unit_year.id]))
