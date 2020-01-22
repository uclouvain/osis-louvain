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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase

from base.business import learning_unit_year_with_context
from base.enums.component_detail import VOLUME_TOTAL, VOLUME_Q1, VOLUME_Q2, VOLUME_REQUIREMENT_ENTITY
from base.models.enums import organization_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.organization import OrganizationFactory
from reference.tests.factories.country import CountryFactory


class LearningUnitYearWithContextTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.organization = OrganizationFactory(type=organization_type.MAIN)
        cls.country = CountryFactory()
        cls.entity = EntityFactory(country=cls.country, organization=cls.organization)
        cls.learning_container_yr = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            requirement_entity=cls.entity
        )
        cls.learning_component_yr = LearningComponentYearFactory(
            learning_unit_year__learning_container_year=cls.learning_container_yr,
            hourly_volume_partial_q1=-1,
            planned_classes=1
        )

    def test_volume_learning_component_year(self):
        self.learning_component_yr.repartition_volume_requirement_entity = 15

        self.learning_component_yr.hourly_volume_total_annual = 15
        self.learning_component_yr.hourly_volume_partial_q1 = 10
        self.learning_component_yr.hourly_volume_partial_q2 = 5
        data = learning_unit_year_with_context.volume_learning_component_year(self.learning_component_yr)
        self.assertEqual(data.get(VOLUME_TOTAL), 15)

        self.assertEqual(data.get(VOLUME_Q1), 10)
        self.assertEqual(data.get(VOLUME_Q2), 5)
        self.assertEqual(data.get(VOLUME_REQUIREMENT_ENTITY), 15)
