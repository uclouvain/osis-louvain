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

from education_group.templatetags.version_details import version_details
from program_management.ddd.domain.node import NodeIdentity
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository

YEAR = 2019


class TestVersionDetails(SimpleTestCase):

    def setUp(self):
        self.root_node_code = 'LCOMI200M'

        self.program_tree = ProgramTreeFactory(
            entity_id__year=YEAR,
            entity_id__code=self.root_node_code,
        )
        self.fake_program_tree_repository = get_fake_program_tree_repository([self.program_tree])

        self.program_tree_version = ProgramTreeVersionFactory(
            tree=self.program_tree,
            entity_id__version_name='CEMS',
            program_tree_repository=self.fake_program_tree_repository,
            title_fr="Title fr",
        )

    def test_version_details(self):
        node_identity = NodeIdentity(code=self.root_node_code, year=YEAR)
        result_data = version_details(node_identity, [self.program_tree_version])
        self.assertEqual(result_data['title'], ' - Title fr')
        self.assertEqual(result_data['version_label'], '[CEMS]')

    def test_no_version(self):
        node_identity = NodeIdentity(code="ANYTHING", year=YEAR)
        result_data = version_details(node_identity, [self.program_tree_version])
        self.assertIsNone(result_data)
