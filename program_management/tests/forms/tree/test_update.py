# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import mock
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from osis_common.ddd.interface import BusinessExceptions
from program_management.forms.tree.update import UpdateLinkForm
from program_management.tests.ddd.factories.link import LinkFactory


class TestUpdateLinkForm(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = LinkFactory()
        super().setUpClass()

    def _get_update_node_form_instance(self, **kwargs):
        return UpdateLinkForm(
            parent_node_code=self.link.parent.code, parent_node_year=self.link.parent.year,
            node_to_update_code=self.link.child.code, node_to_update_year=self.link.child.year,
            data=kwargs
        )

    def test_form_valid(self):
        form_instance = self._get_update_node_form_instance()
        self.assertTrue(form_instance.is_valid())

    def test_form_link_type_invalid(self):
        form_instance = self._get_update_node_form_instance(link_type='invalid')
        self.assertFalse(form_instance.is_valid())
        self.assertTrue(form_instance.errors['link_type'])

    @mock.patch('program_management.ddd.validators._block_validator.BlockValidator.validate')
    def test_form_invalid_with_validator_exception(self, mock_validate):
        error_msg = 'error'
        mock_validate.side_effect = BusinessExceptions(messages=[error_msg])
        form_instance = self._get_update_node_form_instance()
        self.assertFalse(form_instance.is_valid())

    @mock.patch("program_management.ddd.service.write.update_link_service.update_link")
    def test_save_should_call_update_link_service(self, mock_service_update_link):
        form_instance = self._get_update_node_form_instance()
        form_instance.is_valid()
        form_instance.save()
        self.assertTrue(mock_service_update_link.called)
