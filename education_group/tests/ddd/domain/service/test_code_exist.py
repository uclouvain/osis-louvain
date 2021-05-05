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

from education_group.ddd.domain.service.code_exist import CheckCodeExist
from education_group.tests.ddd.factories.group import GroupFactory
from testing.testcases import DDDTestCase


class TestCheckCodeExist(DDDTestCase):
    def test_assert_existing_year(self):
        group = GroupFactory(persist=True)

        result = CheckCodeExist.get_existing_year(group.code)

        self.assertEqual(group.entity_id.year, result)

    def test_assert_none_when_no_existing_year(self):
        self.assertIsNone(CheckCodeExist.get_existing_year("DUMMY"))
