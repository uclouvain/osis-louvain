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
from django.test import TestCase

from education_group.tests.ddd.factories.group import GroupIdentityFactory
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.service.write import prolong_existing_tree_version_service
from program_management.tests.ddd.factories.commands.prolong_existing_program_tree_version import \
    ProlongExistingProgramTreeVersionCommandFactory


# todo do tests
class TestProlongExistingTreeVersion(TestCase):

    @mock.patch(
        "program_management.ddd.domain.service.identity_search.GroupIdentitySearch.get_from_tree_version_identity")
    @mock.patch(
        "program_management.ddd.service.write.extend_existing_tree_version_service.extend_existing_past_version")
    @mock.patch("program_management.ddd.service.write.update_program_tree_version_service.update_program_tree_version")
    @mock.patch(
        "program_management.ddd.service.write.postpone_tree_specific_version_service.postpone_program_tree_version")
    def test_should_call_update_group_service_and_update_tree_version_service(
            self,
            mock_postpone_program_tree_version,
            mock_update_program_tree_version,
            mock_extend_existing_past_version,
            mock_get_from_tree_version_identity
    ):
        cmd = ProlongExistingProgramTreeVersionCommandFactory()
        identity_expected = ProgramTreeVersionIdentity(
            version_name=cmd.version_name,
            offer_acronym=cmd.offer_acronym,
            year=cmd.updated_year,
            transition_name=cmd.transition_name,
        )

        mock_extend_existing_past_version.return_value = [identity_expected]
        mock_get_from_tree_version_identity.return_value = GroupIdentityFactory(year=cmd.updated_year)

        result = prolong_existing_tree_version_service.prolong_existing_tree_version(cmd)

        self.assertTrue(mock_extend_existing_past_version.called)
        self.assertTrue(mock_update_program_tree_version.called)
        self.assertTrue(mock_postpone_program_tree_version.called)

        self.assertEqual(result, [identity_expected])
