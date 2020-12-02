##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import SimpleTestCase

from base.forms.utils.acronym_field import AcronymField, _create_first_letter_choices


class TestAcronymField(SimpleTestCase):
    def test_initialize(self):
        field = AcronymField()
        first_letter_widget = field.widget.widgets[0]
        self.assertEqual(first_letter_widget.choices, list(_create_first_letter_choices()))

    def test_compress(self):
        field = AcronymField()
        result = field.compress(['L', 'DROIT'])
        self.assertEqual(result, 'LDROIT')

    def test_field_not_required(self):
        field = AcronymField(required=False)
        self.assertFalse(all(f.required for f in field.fields))

    def test_field_not_disabled(self):
        field = AcronymField(disabled=True)
        self.assertTrue(all(f.disabled for f in field.fields))

    def test_field_clean(self):
        field = AcronymField()
        first_letter_widget = field.widget.widgets[0]
        self.assertEqual(first_letter_widget.choices, list(_create_first_letter_choices()))
        self.assertEqual(field.clean(['L', 'DROIT']), 'LDROIT')
