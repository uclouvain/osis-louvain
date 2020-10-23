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
from django.test import TestCase

from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.tests.factories.element import ElementGroupYearFactory


class TestNodeIdentitySearchGetFromElementId(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.element_group_year = ElementGroupYearFactory()

    def test_assert_instance_of_node_identity(self):
        node_id = NodeIdentitySearch.get_from_element_id(element_id=self.element_group_year.pk)

        self.assertIsInstance(node_id, NodeIdentity)
        self.assertEqual(
            node_id,
            NodeIdentity(
                code=self.element_group_year.group_year.partial_acronym,
                year=self.element_group_year.group_year.academic_year.year
            )
        )

    def test_assert_none_return_when_no_occurence_found(self):
        node_id = NodeIdentitySearch.get_from_element_id(element_id=-100)
        self.assertIsNone(node_id)
