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
from unittest import skip

import attr
from django.test import override_settings

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from program_management.ddd import command
from program_management.ddd.domain.exception import CannotDetachOptionsException, \
    MinimumChildTypesNotRespectedException, CannotDetachRootException, MinimumEditableYearException
from program_management.ddd.domain.link import LinkIdentity
from program_management.ddd.domain.program_tree import build_path
from program_management.ddd.service.write import detach_node_service
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS1BA import OSIS1BAFactory
from program_management.tests.ddd.factories.domain.program_tree_version.training.OSIS2M import OSIS2MFactory
from testing.testcases import DDDTestCase


class TestDetachNode(DDDTestCase):
    def setUp(self):
        super().setUp()
        self.bachelor = OSIS1BAFactory()[0].tree
        path = build_path(
            self.bachelor.root_node,
            self.bachelor.get_node_by_code_and_year("LOSIS101T", 2018),
            self.bachelor.get_node_by_code_and_year("LOSIS101R", 2018),
            self.bachelor.get_node_by_code_and_year("LSINF1002", 2018),
        )
        self.cmd = command.DetachNodeCommand(path=path, commit=True)

    def test_cannot_detach_option_which_is_used_by_finality(self):
        master_2m = OSIS2MFactory()[0].tree
        path = build_path(
            master_2m.root_node,
            master_2m.get_node_by_code_and_year("LOSIS106G", 2018),
            master_2m.get_node_by_code_and_year("LOSIS200O", 2018),
        )
        cmd = attr.evolve(self.cmd, path=path)

        with self.assertRaisesBusinessException(CannotDetachOptionsException):
            detach_node_service.detach_node(cmd)

    @skip("Define prerequisites repository")
    def test_cannot_detach_learning_unit_which_is_a_prerequisite(self):
        with self.assertRaisesBusinessException(MultipleBusinessExceptions):
            detach_node_service.detach_node(self.cmd)

    def test_cannot_detach_mandatory_children(self):
        path = build_path(
            self.bachelor.root_node,
            self.bachelor.get_node_by_code_and_year("LOSIS101T", 2018),
        )
        cmd = attr.evolve(self.cmd, path=path)

        with self.assertRaisesBusinessException(MinimumChildTypesNotRespectedException):
            detach_node_service.detach_node(cmd)

    @skip("Code breaks when path is root node")
    def test_cannot_detach_root_from_tree(self):
        path = build_path(self.bachelor.root_node)
        cmd = attr.evolve(self.cmd, path=path)

        with self.assertRaisesBusinessException(CannotDetachRootException):
            detach_node_service.detach_node(cmd)

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2019)
    def test_cannot_detach_from_tree_before_minimum_editable_year(self):
        with self.assertRaisesBusinessException(MinimumEditableYearException):
            detach_node_service.detach_node(self.cmd)

    def test_should_return_link_identity_of_link_deleted(self):
        result = detach_node_service.detach_node(self.cmd)

        expected = LinkIdentity(parent_code="LOSIS101R", child_code="LSINF1002", parent_year=2018, child_year=2018)
        self.assertEqual(expected, result)
