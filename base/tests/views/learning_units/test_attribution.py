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
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.models.person import Person
from base.tests.factories.learning_component_year import LecturingLearningComponentYearFactory, \
    PracticalLearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory, LearningUnitYearPartimFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from attribution.views.attribution import get_charge_repartition_warning_messages


class TestViewAttributions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('can_access_learningunit')

        cls.luy_without_attribution = LearningUnitYearFullFactory()

        cls.luy = LearningUnitYearFullFactory()

        cls.lecturing_component = LecturingLearningComponentYearFactory(
            learning_unit_year=cls.luy)
        cls.practical_component = PracticalLearningComponentYearFactory(
            learning_unit_year=cls.luy)
        cls.attribution = AttributionNewFactory(
            learning_container_year=cls.luy.learning_container_year
        )
        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.lecturing_component
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution,
            learning_component_year=cls.practical_component
        )

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_when_no_attributions_for_learning_unit(self):
        url = reverse("learning_unit_attributions", args=[self.luy_without_attribution.id])

        response = self.client.get(url)
        self.assertTemplateUsed(response, "learning_unit/attributions.html")

        context = response.context
        self.assertQuerysetEqual(context["attributions"], [])
        self.assertFalse(context["can_manage_charge_repartition"])
        self.assertFalse(context["can_manage_attribution"])
        self.assertEqual(context["learning_unit_year"], self.luy_without_attribution)

    def test_when_attributions_for_learning_unit(self):
        url = reverse("learning_unit_attributions", args=[self.luy.id])

        response = self.client.get(url)
        self.assertTemplateUsed(response, "learning_unit/attributions.html")

        context = response.context
        self.assertQuerysetEqual(context["attributions"], [self.attribution], transform=lambda obj: obj)
        self.assertEqual(context["learning_unit_year"], self.luy)


class TestGetChargeRepartitionWarningMessage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.full_luy = LearningUnitYearFullFactory()
        cls.partim_luy_1 = LearningUnitYearPartimFactory(academic_year=cls.full_luy.academic_year,
                                                         learning_container_year=cls.full_luy.learning_container_year)
        cls.partim_luy_2 = LearningUnitYearPartimFactory(academic_year=cls.full_luy.academic_year,
                                                         learning_container_year=cls.full_luy.learning_container_year)
        cls.attribution_full = AttributionNewFactory(
            learning_container_year=cls.full_luy.learning_container_year
        )
        cls.full_lecturing_component = LecturingLearningComponentYearFactory(learning_unit_year=cls.full_luy)
        cls.full_practical_component = PracticalLearningComponentYearFactory(learning_unit_year=cls.full_luy)

        cls.partim_1_lecturing_component = \
            LecturingLearningComponentYearFactory(learning_unit_year=cls.partim_luy_1)
        cls.partim_1_practical_component = \
            PracticalLearningComponentYearFactory(learning_unit_year=cls.partim_luy_1)

        cls.partim_2_lecturing_component = \
            LecturingLearningComponentYearFactory(learning_unit_year=cls.partim_luy_2)
        cls.partim_2_practical_component = \
            PracticalLearningComponentYearFactory(learning_unit_year=cls.partim_luy_2)

        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution_full,
            learning_component_year=cls.full_lecturing_component,
            allocation_charge=20
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution_full,
            learning_component_year=cls.full_practical_component,
            allocation_charge=20
        )

        cls.attribution_partim_1 = cls.attribution_full
        cls.attribution_partim_1.id = None
        cls.attribution_partim_1.save()

        cls.attribution_partim_2 = cls.attribution_full
        cls.attribution_partim_2.id = None
        cls.attribution_partim_2.save()

    def setUp(self):
        self.charge_lecturing_1 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_1,
            learning_component_year=self.partim_1_lecturing_component,
            allocation_charge=10
        )
        self.charge_practical_1 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_1,
            learning_component_year=self.partim_1_practical_component,
            allocation_charge=10
        )

        self.charge_lecturing_2 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_2,
            learning_component_year=self.partim_2_lecturing_component,
            allocation_charge=10
        )
        self.charge_practical_2 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_2,
            learning_component_year=self.partim_2_practical_component,
            allocation_charge=10
        )

    def test_should_not_give_warning_messages_when_volume_partim_inferior_or_equal_to_volume_parent(self):
        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)

        self.assertEqual(msgs,
                         [])

    def test_should_not_fail_when_no_charges(self):
        self.charge_lecturing_1.allocation_charge = None
        self.charge_lecturing_1.save()
        self.charge_lecturing_2.allocation_charge = None
        self.charge_lecturing_2.save()
        self.charge_practical_1.allocation_charge = None
        self.charge_practical_1.save()
        self.charge_practical_2.allocation_charge = None
        self.charge_practical_2.save()

        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)

        self.assertEqual(msgs,
                         [])

    def test_should_give_warning_messages_when_volume_partim_superior_to_volume_parent(self):
        self.charge_lecturing_1.allocation_charge = 50
        self.charge_lecturing_1.save()

        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)
        tutor_name = Person.get_str(self.attribution_full.tutor.person.first_name,
                                    self.attribution_full.tutor.person.middle_name,
                                    self.attribution_full.tutor.person.last_name)
        tutor_name_with_function = "{} ({})".format(tutor_name, _(self.attribution_full.get_function_display()))
        self.assertListEqual(msgs, [_("The sum of volumes for the partims for professor %(tutor)s is superior to the "
                                      "volume of parent learning unit for this professor") % {
                                        "tutor": tutor_name_with_function}])
