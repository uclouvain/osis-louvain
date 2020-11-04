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
from unittest.mock import patch

from django.test import SimpleTestCase

from education_group.ddd import command
from education_group.ddd.service.read import get_group_service


class TestGetGroup(SimpleTestCase):
    def setUp(self):
        self.cmd = command.GetGroupCommand(year=2018, code="LTRONC1")

    def test_assert_repository_called(self):
        with patch('education_group.ddd.service.read.get_group_service.GroupRepository.get') as mock_grp_repo_get:
            get_group_service.get_group(self.cmd)
            self.assertTrue(mock_grp_repo_get.called)
