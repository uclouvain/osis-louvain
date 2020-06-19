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
from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy as _

from program_management.ddd.validators._detach_root import DetachRootValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin


class TestDetachRoot(TestValidatorValidateMixin, SimpleTestCase):
    def setUp(self) -> None:
        self.tree = ProgramTreeFactory()
        self.link = LinkFactory(parent=self.tree.root_node)

    def test_should_raise_exception_when_node_to_detach_is_root(self):
        root_path = str(self.tree.root_node.node_id)
        validator = DetachRootValidator(self.tree, root_path)
        self.assertValidatorRaises(validator, [_("Cannot perform detach action on root.")])

    def test_should_not_raise_exception_when_node_to_detach_is_not_root(self):
        child_root_path = "|".join([str(self.tree.root_node.node_id), str(self.link.child.node_id)])
        validator = DetachRootValidator(self.tree, child_root_path)
        self.assertValidatorNotRaises(validator)
