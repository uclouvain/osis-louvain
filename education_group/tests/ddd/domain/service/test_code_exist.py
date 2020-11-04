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

from education_group.ddd.domain.service.code_exist import CheckCodeExist
from education_group.tests.factories.group_year import GroupYearFactory


class TestCheckCodeExist(TestCase):
    def test_assert_existing_year(self):
        group_db_obj = GroupYearFactory(academic_year__year=2020)
        self.assertEqual(CheckCodeExist.get_existing_year(group_db_obj.partial_acronym), 2020)

    def test_assert_none_when_no_existing_year(self):
        self.assertIsNone(CheckCodeExist.get_existing_year("DUMMY"))
