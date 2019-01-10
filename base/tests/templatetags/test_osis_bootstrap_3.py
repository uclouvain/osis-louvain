##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
################################################################################
from bootstrap3.templatetags import bootstrap3
from django import forms
from django.test import SimpleTestCase

from base.templatetags.osis_bootstrap3 import bootstrap_row


class TestForm(forms.Form):
    text = forms.CharField(max_length=10)
    number = forms.IntegerField()


class TestBootstrapRow(SimpleTestCase):
    def setUp(self):
        self.form = TestForm()

    def test_should_return_empty_string_when_no_arguments_given(self):
        expected = ""
        result = bootstrap_row()
        self.assertEqual(result, expected)

    def test_should_return_empty_string_when_field_is_none(self):
        expected = ""
        result = bootstrap_row(field_0=None)
        self.assertEqual(result, expected)

    def test_should_return_row_with_single_bootstrap_field(self):
        expected = '<div class="form-group row">\n' + \
                   "\t" + bootstrap3.bootstrap_field(field=self.form["text"], show_help=False) + "\n" + \
                   "</div>"
        result = bootstrap_row(field_0=self.form["text"], show_help_0=False)
        self.assertEqual(result, expected)

    def test_should_return_row_with_multiple_bootstrap_field(self):
        expected = '<div class="form-group row">\n' + \
                   "\t" + bootstrap3.bootstrap_field(field=self.form["text"], form_group_class="col-md-4") + "\n" + \
                   "\t" + bootstrap3.bootstrap_field(field=self.form["number"], form_group_class="col-md-6") + "\n" + \
                   "</div>"
        result = bootstrap_row(field_1=self.form["number"], form_group_class_0="col-md-4", field_0=self.form["text"],
                               form_group_class_1="col-md-6")

        self.assertEqual(result, expected)

    def test_should_not_take_into_account_none_field(self):
        expected = '<div class="form-group row">\n' + \
                   "\t" + bootstrap3.bootstrap_field(field=self.form["text"]) + "\n" + \
                   "\t" + bootstrap3.bootstrap_field(field=self.form["number"]) + "\n" + \
                   "</div>"
        result = bootstrap_row(field_0=self.form["text"], field_1=None, field_2=self.form["number"])

        self.assertEqual(result, expected)
