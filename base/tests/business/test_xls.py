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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from base.business.xls import convert_boolean, _get_all_columns_reference, get_entity_version_xls_repr
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_version import EntityVersionFactory


class TestXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()
        cls.academic_year = create_current_academic_year()
        cls.entity = EntityVersionFactory()

    def test_convert_boolean(self):
        self.assertEqual(convert_boolean(None), _('no'))
        self.assertEqual(convert_boolean(True), _('yes'))
        self.assertEqual(convert_boolean(False), _('no'))

    def test_get_all_columns_reference(self):
        self.assertCountEqual(_get_all_columns_reference(0), [])
        self.assertCountEqual(_get_all_columns_reference(2), ['A', 'B'])

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_get_active_entity_version_xls_repr(self, mock_entity_is_active):
        acronym = self.entity.acronym
        self.assertEqual(
            get_entity_version_xls_repr(acronym, self.academic_year.year), acronym
        )

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=False)
    def test_get_inactive_entity_version_xls_repr(self, mock_entity_is_active):
        acronym = self.entity.acronym
        self.assertEqual(
            get_entity_version_xls_repr(acronym, self.academic_year.year), '\u0336'.join(acronym) + '\u0336'
        )
