##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
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
from unittest import mock

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory


class TestRenderToExcelMixin:
    """
        Mixin to test that a view generate the appropriate xls file depending on the value of
        the parameter "xls_status".

    """
    url = None
    get_data = {}
    tuples_xls_status_value_with_xls_method_function = ()

    def test_generate_xls_according_to_value_of_xls_status_parameter(self):
        for xls_status_value, xls_function in self.tuples_xls_status_value_with_xls_method_function:
            with self.subTest(xls_status_value=xls_status_value):
                self.xls_create_patcher = mock.patch(xls_function, return_value=HttpResponse())
                self.mocked_xls_function = self.xls_create_patcher.start()

                get_data = self.get_data.copy()
                get_data["xls_status"] = xls_status_value
                self.client.get(self.url, data=get_data)

                self.assertTrue(self.mocked_xls_function.called)

                self.xls_create_patcher.stop()
