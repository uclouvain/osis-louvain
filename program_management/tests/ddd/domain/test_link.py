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

from base.models.enums.link_type import LinkTypes
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestIsReference(SimpleTestCase):
    def test_when_link_type_is_reference(self):
        link = LinkFactory(link_type=LinkTypes.REFERENCE)
        self.assertTrue(link.is_reference())

    def test_when_link_type_is_none(self):
        link = LinkFactory(link_type=None)
        self.assertFalse(link.is_reference())


class TestStr(SimpleTestCase):
    def test_str(self):
        link = LinkFactory(
            parent=NodeGroupYearFactory(acronym='parent', year=2019),
            child=NodeLearningUnitYearFactory(acronym='child', year=2018)
        )
        expected_result = 'parent (2019) - child (2018)'
        self.assertEqual(expected_result, str(link))
