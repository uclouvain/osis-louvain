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
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase

from base.management.commands import load_extra_data_from_xls
from base.models.entity import Entity
from base.models.person import Person
from base.models.person_entity import PersonEntity
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory


class TestGetModelClassFromWorksheetTitle(TestCase):
    """Unit tests on _get_model_class_from_worksheet_title()"""

    def test_without_alias(self):
        worksheet = Mock(title='base.PersonEntity')
        result = load_extra_data_from_xls.Command._get_model_class_from_worksheet_title(worksheet)
        self.assertEqual(result, PersonEntity)

    def test_when_app_does_not_exist(self):
        worksheet = Mock(title='inexisting_app.InexistingModel')
        result = load_extra_data_from_xls.Command._get_model_class_from_worksheet_title(worksheet)
        self.assertIsNone(result)


class TestSaveInDatabase(TestCase):
    """Unit tests on _save_in_database()"""

    def setUp(self):
        self.command_instance = load_extra_data_from_xls.Command()
        self.headers = [
            (0, 'entity__entityversion__acronym',),
            (1, 'person__user__username',),
        ]
        self.entity_version = EntityVersionFactory(acronym='ESPO')
        self.person = PersonFactory(user__username='toto')
        self.xls_row = [
            Mock(value=self.entity_version.acronym),
            Mock(value=self.person.user.username),
        ]

    def test_when_entity_manager_obj_does_not_exist(self):
        obj, created = self.command_instance._save_in_database(self.xls_row, PersonEntity, self.headers)
        self.assertTrue(created)
        self.assertTrue(obj.entity.entityversion_set.filter(acronym=self.entity_version.acronym).exists())
        self.assertEqual(obj.person.user.username, self.person.user.username)

    def test_when_entity_does_not_exist(self):
        self.entity_version.delete()
        with self.assertRaises(Entity.DoesNotExist):
            obj, created = self.command_instance._save_in_database(self.xls_row, PersonEntity, self.headers)

    def test_when_person_does_not_exist(self):
        """Test on get() into foreign key"""
        self.person.delete()
        with self.assertRaises(Person.DoesNotExist):
            obj, created = self.command_instance._save_in_database(self.xls_row, PersonEntity, self.headers)

    def test_when_user_does_not_exists(self):
        """Test on get() into foreign key of foreign key"""
        User.objects.filter(id=self.person.user_id).delete()
        with self.assertRaises(User.DoesNotExist):
            obj, created = self.command_instance._save_in_database(self.xls_row, PersonEntity, self.headers)

    def test_when_entity_manager_obj_exists(self):
        PersonEntityFactory(
            entity=self.entity_version.entity,
            person=self.person,
        )
        obj, created = self.command_instance._save_in_database(self.xls_row, PersonEntity, self.headers)
        self.assertFalse(created)


class TestFindObjectTroughForeignKeys(TestSaveInDatabase):
    """Unit tests on _find_object_through_foreign_keys()"""

    def setUp(self):
        super(TestFindObjectTroughForeignKeys, self).setUp()
        self.field = self.headers[1][1]  # 'person__user__username'
        self.value = self.person.user.username

    def test_classic_usage(self):
        result = self.command_instance._find_object_through_foreign_keys(PersonEntity, self.field, self.value)
        expected_result = ('person', self.person)
        self.assertEqual(result, expected_result)

    def test_when_field_is_natural_key(self):
        field_as_natural_key = self.field + load_extra_data_from_xls.NATURAL_KEY_IDENTIFIER
        result = self.command_instance._find_object_through_foreign_keys(PersonEntity, field_as_natural_key, self.value)
        expected_result = ('person**', self.person)
        self.assertEqual(result, expected_result)


class TestConvertBooleanVellValue(TestCase):
    """Unit tests on _convert_boolean_cell_value()"""

    def test_when_value_is_true(self):
        result = load_extra_data_from_xls.Command._convert_boolean_cell_value(True)
        self.assertTrue(result)

        result = load_extra_data_from_xls.Command._convert_boolean_cell_value("True")
        self.assertTrue(result)

    def test_when_value_is_false(self):
        result = load_extra_data_from_xls.Command._convert_boolean_cell_value(False)
        self.assertFalse(result)

        result = load_extra_data_from_xls.Command._convert_boolean_cell_value("False")
        self.assertFalse(result)

    def test_when_value_is_no_boolean(self):
        result = load_extra_data_from_xls.Command._convert_boolean_cell_value("something else")
        self.assertFalse(isinstance(result, bool))


class TestCleanHeaderFromSpecialChars(TestCase):
    """Unit tests on _clean_header_from_special_chars()"""

    def test(self):
        col_name = "i_am_field_composing_natural_key**"
        result = load_extra_data_from_xls.Command._clean_header_from_special_chars(col_name)
        self.assertEqual(result, "i_am_field_composing_natural_key")
