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
import mock
from django.test import SimpleTestCase

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_role.contrib.admin import RoleModelAdmin, EntityRoleModelAdmin


class TestRoleModelAdmin(SimpleTestCase):
    def test_ensure_list_display(self):
        expected_list_display = ('person',)
        self.assertEquals(RoleModelAdmin.list_display, expected_list_display)

    def test_ensure_search_fields(self):
        expected_search_fields = ['person__first_name', 'person__last_name', ]
        self.assertListEqual(RoleModelAdmin.search_fields, expected_search_fields)


class TestEntityRoleModelAdmin(SimpleTestCase):
    def test_ensure_list_display(self):
        expected_list_display = ('person', 'entity', 'latest_entity_version_name', 'with_child', )
        self.assertEquals(EntityRoleModelAdmin.list_display, expected_list_display)

    def test_ensure_search_fields(self):
        expected_search_fields = [
            'person__first_name',
            'person__last_name',
            'entity__entityversion__acronym'
        ]
        self.assertListEqual(EntityRoleModelAdmin.search_fields, expected_search_fields)

    @mock.patch('base.models.entity_version.get_last_version', return_value=None)
    def test_latest_entity_version_name_case_not_found(self, mock_get_last_version):
        result_str = EntityRoleModelAdmin.latest_entity_version_name(
            mock.Mock(spec=EntityRoleModelAdmin),
            mock.Mock(**{'entity': mock.PropertyMock(return_value=EntityFactory.build())})
        )
        self.assertEquals(result_str, 'Not found')

    @mock.patch('base.models.entity_version.get_last_version')
    def test_latest_entity_version_name_case_found(self, mock_get_last_version):
        entity_version = EntityVersionFactory.build()
        mock_get_last_version.return_value = entity_version

        result_str = EntityRoleModelAdmin.latest_entity_version_name(
            mock.Mock(spec=EntityRoleModelAdmin),
            mock.Mock(**{'entity': mock.PropertyMock(return_value=EntityFactory.build())})
        )
        self.assertEquals(result_str, entity_version.acronym)
