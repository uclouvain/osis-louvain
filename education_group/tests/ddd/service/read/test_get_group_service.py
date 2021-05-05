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

from education_group.ddd import command
from education_group.ddd.domain import exception
from education_group.ddd.service.read import get_group_service
from education_group.tests.ddd.factories.group import GroupFactory
from testing.testcases import DDDTestCase


class TestGetGroup(DDDTestCase):
    def setUp(self):
        super().setUp()
        self.group = GroupFactory(persist=True)
        self.cmd = command.GetGroupCommand(year=self.group.year, code=self.group.code)

    def test_throw_exception_when_no_matching_group(self):
        cmd = command.GetGroupCommand(year=self.group.year + 1, code=self.group.code)
        with self.assertRaisesBusinessException(exception.GroupNotFoundException):
            get_group_service.get_group(cmd)

    def test_return_matching_group(self):
        result = get_group_service.get_group(self.cmd)
        self.assertEqual(self.group, result)
