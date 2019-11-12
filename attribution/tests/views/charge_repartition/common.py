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
from unittest.mock import patch

from attribution.models.attribution_new import AttributionNew
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.tests.factories.learning_component_year import LecturingLearningComponentYearFactory, \
    PracticalLearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory, LearningUnitYearPartimFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.views.mixins import RulesRequiredMixin


class TestChargeRepartitionMixin:
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year = LearningUnitYearPartimFactory()
        cls.lecturing_component = LecturingLearningComponentYearFactory(learning_unit_year=cls.learning_unit_year)
        cls.practical_component = PracticalLearningComponentYearFactory(learning_unit_year=cls.learning_unit_year)

        cls.full_learning_unit_year = LearningUnitYearFullFactory(
            learning_container_year=cls.learning_unit_year.learning_container_year,
            academic_year=cls.learning_unit_year.academic_year
        )
        cls.lecturing_component_full = LecturingLearningComponentYearFactory(
            learning_unit_year=cls.full_learning_unit_year
        )
        cls.practical_component_full = PracticalLearningComponentYearFactory(
            learning_unit_year=cls.full_learning_unit_year
        )
        cls.person = PersonWithPermissionsFactory('can_access_learningunit')

    def setUp(self):
        self.attribution = AttributionNewFactory(
            learning_container_year=self.learning_unit_year.learning_container_year
        )
        attribution_id = self.attribution.id
        self.charge_lecturing = AttributionChargeNewFactory(
            attribution=self.attribution,
            learning_component_year=self.lecturing_component
        )
        self.charge_practical = AttributionChargeNewFactory(
            attribution=self.attribution,
            learning_component_year=self.practical_component
        )

        self.attribution_full = self.attribution
        self.attribution_full.id = None
        self.attribution_full.save()
        self.charge_lecturing_full = AttributionChargeNewFactory(
            attribution=self.attribution_full,
            learning_component_year=self.lecturing_component_full
        )
        self.charge_practical_full = AttributionChargeNewFactory(
            attribution=self.attribution_full,
            learning_component_year=self.practical_component_full
        )

        self.attribution = AttributionNew.objects.get(id=attribution_id)
        self.client.force_login(self.person.user)

        self.patcher = patch.object(RulesRequiredMixin, "test_func", return_value=True)
        self.mocked_permission_function = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def clean_partim_charges(self):
        self.charge_practical.delete()
        self.charge_lecturing.delete()
        self.attribution.delete()
