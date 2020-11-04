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
from types import SimpleNamespace

import mock
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from osis_role.contrib import models
from osis_role.role import OsisRoleManager


class TestOsisRoleManager(SimpleTestCase):
    def setUp(self):
        self.manager = OsisRoleManager()

    def test_register_case_not_subclass_of_role_model(self):
        with self.assertRaises(ImproperlyConfigured):
            self.manager.register(SimpleNamespace)

    def test_register_case_subclass_of_role_model(self, ):
        subclass = mock.Mock(spec=models.RoleModel)
        type(subclass.__class__).group_name = mock.PropertyMock(return_value='role_model_subclass')

        self.manager.register(subclass.__class__)
        self.assertIsInstance(self.manager.roles, set)
        self.assertTrue(subclass.__class__ in self.manager.roles)

    @mock.patch('osis_role.role.OsisRoleManager.roles', new_callable=mock.PropertyMock)
    def test_get_group_names_managed(self, mock_roles_set):
        subclass = mock.Mock(spec=models.RoleModel)
        type(subclass.__class__).group_name = mock.PropertyMock(return_value='role_model_subclass')
        mock_roles_set.return_value = {subclass.__class__}

        self.assertEqual(
            self.manager.group_names_managed(),
            {'role_model_subclass'}
        )
