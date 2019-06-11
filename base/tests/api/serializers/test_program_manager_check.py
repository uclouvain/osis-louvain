#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.api.models.program_manager_check import CheckAccessToStudent
from base.api.serializers.program_manager_check import CheckAccessToStudentSerializer


class CheckAccessToStudentSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.check_access_object = CheckAccessToStudent('123456', '123456')
        cls.serializer = CheckAccessToStudentSerializer(cls.check_access_object)

    def test_contains_expected_fields(self):
        expected_fields = [
            'global_id',
            'registration_id',
            'authorized'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)