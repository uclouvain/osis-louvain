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
from django.test import SimpleTestCase

from base.tests.factories.user import UserFactory
from base.utils import cache
from program_management.ddd import command
from program_management.ddd.service.write import cut_element_service
from program_management.models.enums import node_type


class TestCutElementService(SimpleTestCase):
    def test_should_save_element_cut_to_cache(self):
        user_id = 25
        cut_command = command.CutElementCommand(
            user_id=user_id,
            element_code="LOSIS5878",
            element_year=2015,
            path_to_detach="MDRI2547Q|WDNH8957"
        )
        cut_element_service.cut_element_service(cut_command)

        cached_data = cache.ElementCache(user_id).cached_data
        self.assertTrue(cached_data)

        cache.ElementCache(user_id).clear()

