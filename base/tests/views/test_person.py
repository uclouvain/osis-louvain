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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from base.views.person import EmployeeAutocomplete


class TestPersonAutoComplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.jean = PersonFactory(first_name="Jean", last_name="Dupont", middle_name=None, global_id="01456",
                                 employee=True)
        cls.henry = PersonFactory(first_name="Henry", last_name="Arkin", middle_name="De", global_id="025875",
                                  employee=True)
        cls.student = PersonFactory(first_name="Henry", last_name="Dioup", middle_name=None, global_id="488513",
                                    employee=False)

    def test_get_queryset_with_name(self):
        autocomplete_instance = EmployeeAutocomplete()
        autocomplete_instance.q = self.henry.last_name

        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.henry],
            transform=lambda obj: obj
        )

        autocomplete_instance.q = self.jean.last_name
        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.jean],
            transform=lambda obj: obj
        )

    def test_get_queryset_with_global_id(self):
        autocomplete_instance = EmployeeAutocomplete()
        autocomplete_instance.q = self.henry.global_id
        self.assertQuerysetEqual(
            autocomplete_instance.get_queryset(),
            [self.henry],
            transform=lambda obj: obj
        )

    def test_get_result_label(self):
        self.assertEqual(
            EmployeeAutocomplete().get_result_label(self.jean),
            "Dupont Jean"
        )

        self.assertEqual(
            EmployeeAutocomplete().get_result_label(self.henry),
            "Arkin Henry"
        )
