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
from django.test.utils import override_settings
from django.utils.translation import gettext as _

from program_management.ddd.validators._minimum_editable_year import MinimumEditableYearValidator
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestMinimumEditableYearValidator(SimpleTestCase):

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2019)
    def test_when_root_year_is_lower_than_settings(self):
        year = 2010
        tree = ProgramTreeFactory(root_node__year=year)
        validator = MinimumEditableYearValidator(tree, NodeGroupYearFactory(), str(tree.root_node.node_id))
        self.assertFalse(validator.is_valid())
        expected_result = _("Cannot perform action on a education group before %(limit_year)s") % {
            "limit_year": 2019
        }
        self.assertEqual(expected_result, validator.error_messages[0])

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2019)
    def test_when_root_year_is_equal_to_settings(self):
        year = 2019
        tree = ProgramTreeFactory(root_node__year=year)
        validator = MinimumEditableYearValidator(tree, NodeGroupYearFactory(), str(tree.root_node.node_id))
        self.assertTrue(validator.is_valid())

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2019)
    def test_when_root_year_greater_than_settings(self):
        year = 2099
        tree = ProgramTreeFactory(root_node__year=year)
        validator = MinimumEditableYearValidator(tree, NodeGroupYearFactory(), str(tree.root_node.node_id))
        self.assertTrue(validator.is_valid())
