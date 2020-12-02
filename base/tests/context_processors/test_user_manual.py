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

from base.context_processors.user_manual import UserManual, find_contextual_user_manual


class TestFindcontextualUserManual(SimpleTestCase):
    def setUp(self):
        self.default_manual = UserManual(
            name="default",
            url="default_url",
            contextual_paths=[]
        )

        self.manuals = [
            UserManual(
                name="manual_1",
                url="manual_1_url",
                contextual_paths=["view_manual_1", "view_specific"]
            ),
            UserManual(
                name="manual_2",
                url="manual_2_url",
                contextual_paths=["view_manual_2"]
            )
        ]

    def test_when_no_manuals_given(self):
        contextual_manual = find_contextual_user_manual("view_name", [], self.default_manual)
        self.assertEqual(contextual_manual, self.default_manual)

    def test_when_no_manuals_match_view_name(self):
        contextual_manual = find_contextual_user_manual("view_name", self.manuals, self.default_manual)
        self.assertEqual(contextual_manual, self.default_manual)

    def test_when_a_manual_match_view_name(self):
        contextual_manual = find_contextual_user_manual("view_specific", self.manuals, self.default_manual)
        self.assertEqual(contextual_manual, self.manuals[0])
