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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import mock
from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from base.forms.utils import choice_field
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType
from program_management.forms.select_type import SelectTypeForm


class TestSelectTypeForm(SimpleTestCase):
    @mock.patch("program_management.forms.select_type.allowed_children_types_service.get_allowed_child_types",
                return_value=set())
    def test_assert_call_allowed_children_types_service(self, mock_get_allowed_child_types):
        SelectTypeForm(category=Categories.GROUP.name, path_to=None)
        self.assertTrue(mock_get_allowed_child_types.called)

    @mock.patch("program_management.forms.select_type.allowed_children_types_service.get_allowed_child_types")
    def test_assert_name_choice_is_sorted(self, mock_get_allowed_child_types):
        mock_get_allowed_child_types.return_value = {
            GroupType.SUB_GROUP,
            GroupType.COMMON_CORE
        }

        form = SelectTypeForm(category=Categories.GROUP.name, path_to=None)
        self.assertListEqual(
            form.fields['name'].choices,
            [
                (None, choice_field.BLANK_CHOICE_DISPLAY),
                (GroupType.COMMON_CORE.name, GroupType.COMMON_CORE.value),
                (GroupType.SUB_GROUP.name, GroupType.SUB_GROUP.value)
            ]
        )

    @mock.patch("program_management.forms.select_type.allowed_children_types_service.get_allowed_child_types",
                return_value=set())
    def test_assert_label_is_adapted_to_category(self, mock_get_allowed_child_types):
        form = SelectTypeForm(category=Categories.GROUP.name, path_to=None)

        expected_label = _("Which type of %(category)s do you want to create ?") % {
            "category": Categories.GROUP.value
        }
        self.assertEqual(
            form.fields['name'].label,
            expected_label
        )
