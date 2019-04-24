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

from django.test import TestCase
from django.utils import timezone

from attribution.business.attribution_charge_new import find_attribution_charge_new_by_learning_unit_year_as_dict
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestAttributionChargeNew(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(year=timezone.now().year)
        self.l_unit_1 = LearningUnitYearFactory(acronym="LBIR1212", academic_year=self.academic_year,
                                                subtype=learning_unit_year_subtypes.FULL)
        component = LearningComponentYearFactory(learning_unit_year=self.l_unit_1)
        self.attribution_charge_news = [
            AttributionChargeNewFactory(learning_component_year=component) for _ in range(5)
        ]

    def test_find_attribution_charge_new_by_learning_unit_year(self):
        result = find_attribution_charge_new_by_learning_unit_year_as_dict(self.l_unit_1)
        self.assertEqual(len(result), 5)
