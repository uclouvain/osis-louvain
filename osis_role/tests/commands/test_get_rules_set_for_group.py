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
import io
import json
import sys

import mock
from django.test import TestCase

from osis_role.management.commands import get_rules_set_for_group


class TestRulesSetCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.command_instance = get_rules_set_for_group.Command()

        # mock data stream to be opened as a file
        cls.group, cls.perm, cls.app, cls.ctx = ['dummy_{}'.format(name) for name in ["group", "perm", "app", "ctx"]]
        groups_fixture = json.dumps(
            [{"fields": {"name": cls.group, "permissions": [[cls.perm, cls.app, cls.ctx]]}}]
        )
        cls.mock_open = mock.mock_open(read_data=groups_fixture)

        # redirect stdout to capture print
        cls.output = io.StringIO()
        sys.stdout = cls.output

    def test_generate_rules_set_from_existing_group(self):
        with mock.patch('builtins.open', self.mock_open):
            self.command_instance.handle(group=self.group)
            self.assertIn("'{}.{}': rules.always_allow,".format(self.app, self.perm), self.output.getvalue())

    def test_error_when_no_group_provided_as_arg(self):
        self.command_instance.handle(group=None)
        self.assertIn("Please provide group", self.output.getvalue())

    def test_permissions_for_group_not_found(self):
        with mock.patch('builtins.open', self.mock_open):
            group = 'non_existent_group'
            self.command_instance.handle(group=group)
            self.assertIn('Permissions for group {} not found'.format(group), self.output.getvalue())
