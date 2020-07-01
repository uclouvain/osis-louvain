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
import random

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.forms.education_group.coorganization import CoorganizationEditForm, OrganizationFormset
from base.models.enums import education_group_categories, diploma_coorganization
from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.person import CentralManagerForUEFactory
from base.tests.factories.user import UserFactory
from reference.tests.factories.country import CountryFactory


class TestCoorganizationForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = CentralManagerForUEFactory(user=cls.user)

        cls.academic_year = create_current_academic_year()
        cls.education_group_yr = EducationGroupYearFactory(
            acronym='ARKE2A', academic_year=cls.academic_year,
            education_group_type=EducationGroupTypeFactory(category=education_group_categories.TRAINING),
            management_entity=EntityFactory()
        )

        cls.root_id = cls.education_group_yr.id
        cls.country_be = CountryFactory(iso_code='BE', name='Belgium')

        cls.organization_address = OrganizationAddressFactory(country=cls.country_be)
        cls.organization = cls.organization_address.organization
        cls.education_group_organization = EducationGroupOrganizationFactory(
            organization=cls.organization,
            education_group_year=cls.education_group_yr,
            diploma=diploma_coorganization.UNIQUE,
            all_students=True,
        )
        cls.organization_bis = OrganizationFactory()
        cls.address = OrganizationAddressFactory(organization=cls.organization_bis, is_main=True)

    def setUp(self):
        self.client.force_login(self.user)
        self.data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-diploma': random.choice(DiplomaCoorganizationTypes.get_names()),
            'form-0-country': self.address.country.pk,
            'form-0-organization': self.organization_bis.pk
        }

    def test_fields(self):
        form = CoorganizationEditForm(None, instance=self.education_group_organization, user=self.user)
        expected_fields = [
            'country',
            'organization',
            'all_students',
            'enrollment_place',
            'diploma',
            'is_producing_cerfificate',
            'is_producing_annexe',
        ]
        actual_fields = list(form.fields.keys())

        self.assertListEqual(expected_fields, actual_fields)
        self.assertEqual(form['country'].value(), self.organization_address.country.pk)
        self.assertEqual(form['organization'].value(), self.education_group_organization.organization.pk)
        self.assertEqual(form['diploma'].value(), diploma_coorganization.UNIQUE)
        self.assertTrue(form['all_students'].value())
        self.assertFalse(form['enrollment_place'].value())
        self.assertFalse(form['is_producing_cerfificate'].value())
        self.assertFalse(form['is_producing_annexe'].value())

    def test_formset_valid(self):
        form = OrganizationFormset(
            data=self.data,
            form_kwargs={'education_group_year': EducationGroupYearFactory(), 'user': self.user},
        )
        self.assertTrue(form.is_valid())

    def test_formset_missing_diploma(self):
        self.data['form-0-diploma'] = None
        form = OrganizationFormset(
            data=self.data,
            form_kwargs={'education_group_year': EducationGroupYearFactory(), 'user': self.user},
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(
            form.errors,
            [
                {'diploma': [_("This field is required.")]}
            ]
        )

    def test_formset_with_organization_already_attached_to_egy(self):
        egy = EducationGroupYearFactory()
        egy_organization = EducationGroupOrganizationFactory(
            organization=self.organization_bis,
            education_group_year=egy
        )
        self.data['form-0-organization'] = egy_organization.organization.pk

        form = OrganizationFormset(
            data=self.data,
            form_kwargs={'education_group_year': egy, 'user': self.user},
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(
            form.errors,
            [
                {'organization': [_('There is already a coorganization with this organization')]}
            ]
        )
