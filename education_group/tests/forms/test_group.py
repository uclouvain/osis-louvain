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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import TestCase

from base.models.enums.education_group_types import GroupType
from base.tests.factories.person import PersonFactory
from education_group.forms.group import GroupUpdateForm


class TestGroupUpdateForm(TestCase):
    def setUp(self) -> None:
        self.person = PersonFactory()
        self.form = GroupUpdateForm(user=self.person.user, group_type=GroupType.COMMON_CORE.name)

    def test_assert_code_is_disabled(self):
        self.assertTrue(self.form.fields['code'].disabled)
        self.assertFalse(self.form.fields['code'].required)

    def test_assert_academic_year_is_disabled(self):
        self.assertTrue(self.form.fields['academic_year'].disabled)
        self.assertFalse(self.form.fields['academic_year'].required)
