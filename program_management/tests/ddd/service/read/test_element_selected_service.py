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

from base.utils import cache
from program_management.ddd.service.read import element_selected_service


class TestRetrieveElementsSelected(SimpleTestCase):
    def setUp(self):
        self.user_id = 25
        self.addCleanup(cache.ElementCache(self.user_id).clear)

    def test_should_return_none_if_no_cached_data(self):
        result = element_selected_service.retrieve_element_selected(self.user_id)
        self.assertIsNone(result)

    def test_should_return_cached_data_if_present(self):
        cache.ElementCache(self.user_id).save_element_selected("element_code", 254)

        result = element_selected_service.retrieve_element_selected(self.user_id)
        self.assertEqual(result, cache.ElementCache(self.user_id).cached_data)
