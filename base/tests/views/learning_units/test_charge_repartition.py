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

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from attribution.models.attribution_charge_new import AttributionChargeNew
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


class TestSelectAttributionView(TestChargeRepartitionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.clean_partim_charges()
        self.url = reverse("select_attribution", args=[self.learning_unit_year.id])

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response,  '/login/?next={}'.format(self.url))

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertTrue(self.mocked_permission_function.called)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "learning_unit/select_attribution.html")

    def test_should_give_all_attributions_of_parent_if_no_attribution_in_child(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertQuerysetEqual(
            context["attributions"],
            [self.attribution_full],
            transform=lambda obj: obj
        )

    def test_should_exclude_attributions_for_which_repartition_has_been_done(self):
        attribution = self.attribution_full
        attribution.id = None
        attribution.save()

        charge_lecturing = AttributionChargeNewFactory(
            attribution=attribution,
            learning_component_year=self.lecturing_component
        )
        charge_practical = AttributionChargeNewFactory(
            attribution=attribution,
            learning_component_year=self.practical_component
        )

        response = self.client.get(self.url)

        context = response.context
        self.assertQuerysetEqual(
            context["attributions"],
            []
        )


class TestAddChargeRepartition(TestChargeRepartitionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.clean_partim_charges()
        self.url = reverse("add_charge_repartition", args=[self.learning_unit_year.id, self.attribution_full.id])

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response,  '/login/?next={}'.format(self.url))

    def test_template_used_with_get(self):
        response = self.client.get(self.url)

        self.assertTrue(self.mocked_permission_function.called)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "learning_unit/add_charge_repartition_inner.html")

    def test_post(self):
        data = {
            'lecturing_form-allocation_charge': 50,
            'practical_form-allocation_charge': 10
        }
        response = self.client.post(self.url, data=data)

        AttributionChargeNew.objects.get(learning_component_year=self.lecturing_component,
                                         allocation_charge=50)
        AttributionChargeNew.objects.get(learning_component_year=self.practical_component,
                                         allocation_charge=10)
        AttributionNew.objects.exclude(id=self.attribution_full.id).get(tutor=self.attribution_full.tutor)

        self.assertRedirects(response,
                             reverse("learning_unit_attributions", args=[self.learning_unit_year.id]))


class TestEditChargeRepartition(TestChargeRepartitionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("edit_charge_repartition", args=[self.learning_unit_year.id, self.attribution.id])

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response,  '/login/?next={}'.format(self.url))

    def test_template_used_with_get(self):
        response = self.client.get(self.url)

        self.assertTrue(self.mocked_permission_function.called)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "learning_unit/add_charge_repartition_inner.html")

    def test_post(self):
        data = {
            'lecturing_form-allocation_charge': 50,
            'practical_form-allocation_charge': 10
        }
        response = self.client.post(self.url, data=data)

        self.charge_lecturing.refresh_from_db()
        self.charge_practical.refresh_from_db()
        self.assertEqual(self.charge_lecturing.allocation_charge, 50)
        self.assertEqual(self.charge_practical.allocation_charge, 10)

        self.assertRedirects(response,
                             reverse("learning_unit_attributions", args=[self.learning_unit_year.id]))


class TestRemoveChargeRepartition(TestChargeRepartitionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("remove_attribution", args=[self.learning_unit_year.id, self.attribution.id])

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response,  '/login/?next={}'.format(self.url))

    def test_template_used_with_get(self):
        response = self.client.get(self.url)

        self.assertTrue(self.mocked_permission_function.called)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "learning_unit/remove_charge_repartition_confirmation_inner.html")

    def test_delete_data(self):
        response = self.client.delete(self.url)

        self.assertFalse(AttributionNew.objects.filter(id=self.attribution.id).exists())
        self.assertFalse(
            AttributionChargeNew.objects.filter(id__in=(self.charge_lecturing.id, self.charge_practical.id)).exists()
        )

    def test_delete_redirection(self):
        response = self.client.delete(self.url, follow=False)

        self.assertRedirects(response,
                             reverse("learning_unit_attributions", args=[self.learning_unit_year.id]))
