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
import mock
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums.education_group_types import GroupType, TrainingType
from base.utils.cache import ElementCache
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.views.mixin import ElementSelectedClipBoardSerializer
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory, \
    SpecificProgramTreeVersionFactory


class TestElementSelectedClipBoardSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        request = mock.Mock()
        cls.serializer_instance = ElementSelectedClipBoardSerializer(request)

    def setUp(self) -> None:
        self.cache_element = {
            "action": ElementCache.ElementCacheAction.CUT.value,
            "element_code": "LDROI200A",
            "element_year": 2020
        }

        self.retrieve_element_patcher = mock.patch(
            "education_group.views.mixin.element_selected_service.retrieve_element_selected",
            return_value=self.cache_element
        )
        self.mocked_retrieve_element = self.retrieve_element_patcher.start()
        self.addCleanup(self.retrieve_element_patcher.stop)

    def test_case_no_selected_element(self):
        self.mocked_retrieve_element.return_value = None
        self.assertEqual(
            self.serializer_instance.get_selected_element_clipboard_message(),
            ""
        )

    @mock.patch('education_group.views.mixin.get_group_service.get_group')
    def test_case_group_element_selected(self, mock_get_group_service):
        group = GroupFactory(type=GroupType.COMMON_CORE)
        mock_get_group_service.return_value = group

        expected_result = "<strong>{clipboard_title}</strong><br>{object_str}".format(
            clipboard_title=_("Cut element"),
            object_str="{} - {} - {}".format(group.code, group.abbreviated_title, group.academic_year)
        )
        self.assertEqual(
            self.serializer_instance.get_selected_element_clipboard_message(),
            expected_result
        )

    @mock.patch('education_group.views.mixin.get_program_tree_version_from_node_service.'
                'get_program_tree_version_from_node')
    @mock.patch('education_group.views.mixin.get_group_service.get_group')
    def test_case_standard_version_training_element_selected(
            self,
            mock_get_group_service,
            mock_get_program_tree_version,
    ):
        group = GroupFactory(type=TrainingType.BACHELOR)
        mock_get_group_service.return_value = group

        version = StandardProgramTreeVersionFactory()
        mock_get_program_tree_version.return_value = version

        expected_result = "<strong>{clipboard_title}</strong><br>{object_str}".format(
            clipboard_title=_("Cut element"),
            object_str="{} - {} - {}".format(group.code, group.abbreviated_title, group.academic_year)
        )
        self.assertEqual(
            self.serializer_instance.get_selected_element_clipboard_message(),
            expected_result
        )

    @mock.patch('education_group.views.mixin.get_program_tree_version_from_node_service.'
                'get_program_tree_version_from_node')
    @mock.patch('education_group.views.mixin.get_group_service.get_group')
    def test_case_specific_version_training_element_selected(
            self,
            mock_get_group_service,
            mock_get_program_tree_version,
    ):
        group = GroupFactory(type=TrainingType.BACHELOR)
        mock_get_group_service.return_value = group

        version = SpecificProgramTreeVersionFactory()
        mock_get_program_tree_version.return_value = version

        expected_result = "<strong>{clipboard_title}</strong><br>{object_str}".format(
            clipboard_title=_("Cut element"),
            object_str="{} - {}[{}] - {}".format(
                group.code,
                group.abbreviated_title,
                version.version_name,
                group.academic_year
            )
        )
        self.assertEqual(
            expected_result,
            self.serializer_instance.get_selected_element_clipboard_message()
        )
