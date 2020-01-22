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
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from base.tests.factories.user import UserFactory
from reference.models.country import Country
from rules_management.mixins import PermissionFieldMixin
from rules_management.tests.fatories import PermissionFactory, FieldReferenceFactory


class CountryForm(PermissionFieldMixin, forms.ModelForm):
    context = "LalaLand"

    class Meta:
        model = Country
        fields = "__all__"


class TestPermissionFieldMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.permissions = [PermissionFactory() for _ in range(10)]

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="reference", model="country"),
            field_name="name",
            context="LalaLand",
            permissions=cls.permissions,
        )

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="reference", model="country"),
            field_name="nationality",
            context="",
            permissions=cls.permissions,
        )

        cls.user_with_perm = UserFactory()
        cls.user_with_perm.user_permissions.add(cls.permissions[2])

        cls.user_without_perm = UserFactory()
        cls.user_without_perm.user_permissions.add(PermissionFactory())

    def test_init_with_perm(self):
        form = CountryForm(user=self.user_with_perm)
        self.assertFalse(form.fields['name'].disabled)

    def test_init_without_perm(self):
        form = CountryForm(user=self.user_without_perm)
        self.assertTrue(form.fields['name'].disabled)

    def test_init_without_user(self):
        with self.assertRaises(ImproperlyConfigured):
            CountryForm()

    def test_init_with_context(self):
        form = CountryForm(user=self.user_without_perm, context="HappyLand")
        self.assertFalse(form.fields['name'].disabled)
        self.assertFalse(form.fields['nationality'].disabled)
