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
from unittest import mock

from django.test import TestCase

from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import GroupType
from program_management.ddd import command
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.service.write import create_group_and_attach_service


class TestCreateGroupAndAttachService(TestCase):
    def setUp(self) -> None:
        self.cmd = command.CreateGroupAndAttachCommand(
            code="LTRONC100T",
            type=GroupType.COMMON_CORE.name,
            abbreviated_title="Intitulé en francais",
            title_fr="Titre en français",
            title_en="Title in english",
            credits=30,
            constraint_type=ConstraintTypeEnum.CREDITS.name,
            min_constraint=0,
            max_constraint=20,
            management_entity_acronym="AGRO",
            teaching_campus_name="Mons Fucam",
            organization_name="UCLouvain",
            remark_fr="Remarque en francais",
            remark_en="Remark in english",
            path_to_paste="464656"
        )

    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.node_identity_service')
    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.paste_element_service')
    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.create_group_service')
    def test_assert_call_multiple_services(self, mock_create_group_service, mock_paste_element_service,
                                           mock_node_id_service):
        create_group_and_attach_service.create_group_and_attach(self.cmd)

        self.assertTrue(mock_create_group_service.create_orphan_group.called)
        self.assertTrue(mock_paste_element_service.paste_element.called)
        self.assertTrue(mock_node_id_service.get_node_identity_from_element_id.called)

    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.node_identity_service')
    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.paste_element_service')
    @mock.patch('program_management.ddd.service.write.create_group_and_attach_service.create_group_service')
    def test_assert_start_year_come_from_parent(self,
                                                mock_create_group_service,
                                                mock_paste_element_service,
                                                mock_node_id_service):
        parent_node_id = NodeIdentity(code="LDROI1100", year=2016)
        mock_node_id_service.get_node_identity_from_element_id.return_value = parent_node_id

        create_group_and_attach_service.create_group_and_attach(self.cmd)

        orphan_cmd_called = mock_create_group_service.create_orphan_group.call_args[0][0]
        self.assertEqual(orphan_cmd_called.year, parent_node_id.year)
        self.assertEqual(orphan_cmd_called.start_year, parent_node_id.year)
