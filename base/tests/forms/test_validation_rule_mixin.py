############################################################################
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
############################################################################
from django import forms
from django.core.validators import RegexValidator
from django.test import TestCase

from base.forms.common import ValidationRuleMixin
from base.models.enums.field_status import DISABLED, REQUIRED, ALERT
from base.tests.factories.validation_rule import ValidationRuleFactory
from reference.models.country import Country


class TestForm(ValidationRuleMixin, forms.ModelForm):
    class Meta:
        model = Country
        fields = "__all__"


class TestValidationRuleMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        ValidationRuleFactory(
            field_reference="reference_country.name",
            status_field=DISABLED,
            initial_value="LalaLand",
            placeholder=""
        )

        ValidationRuleFactory(
            field_reference="reference_country.iso_code",
            status_field=REQUIRED,
            initial_value="",
            regex_rule="^(LA|LB)$",
            placeholder="LA"
        )

        ValidationRuleFactory(
            field_reference="reference_country.cref_code",
            status_field=ALERT,
            initial_value="LA",
            regex_rule="^(LA|LB)$",
            placeholder=""
        )

    def test_init(self):
        form = TestForm()
        self.assertFalse(form.fields["name"].required)
        self.assertTrue(form.fields["name"].disabled)
        self.assertEqual(form.fields["name"].initial, "LalaLand")
        with self.assertRaises(KeyError):
            form.fields["name"].widget.attrs['placeholder']

        self.assertTrue(form.fields["iso_code"].required)
        self.assertFalse(form.fields["iso_code"].disabled)
        self.assertIsNone(form.fields["iso_code"].initial)
        self.assertEqual(form.fields["iso_code"].widget.attrs['placeholder'], "LA")
        iso_code_regex_validator = next(
            (validator for validator in form.fields['iso_code'].validators if isinstance(validator, RegexValidator)),
            None
        )
        self.assertIsNotNone(iso_code_regex_validator)

        self.assertFalse(form.fields["cref_code"].required)
        self.assertFalse(form.fields["cref_code"].disabled)
        self.assertTrue(form.fields["cref_code"].warning)
        self.assertEqual(form.fields["cref_code"].initial, "LA")
        cref_code_regex_validator = next(
            (validator for validator in form.fields['iso_code'].validators if isinstance(validator, RegexValidator)),
            None
        )
        self.assertIsNotNone(cref_code_regex_validator)

    def test_is_valid(self):
        form = TestForm(
            data={
                'name': "Zoubiland",
                'iso_code': 'LB',
                'cref_code': 'LA'
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "LalaLand")
        self.assertEqual(form.cleaned_data["iso_code"], "LB")

    def test_is_invalid(self):
        form = TestForm(
            data={
                'name': "Zoubiland",
                'iso_code': 'LZ'
            }
        )
        self.assertFalse(form.is_valid())
