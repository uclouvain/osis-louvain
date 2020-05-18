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
from django.test import SimpleTestCase

from base.ddd.utils.business_validator import BusinessValidator
from base.ddd.utils.validation_message import BusinessValidationMessage, MessageLevel, BusinessValidationMessageList


class ValidatorTest(BusinessValidator):
    success_messages = [
        BusinessValidationMessage('Success msg', MessageLevel.SUCCESS)
    ]

    def validate(self):
        if not self._first_business_validation():
            self.add_error_message("Error message")
        if not self._other_business_validation():
            self.add_messages([
                BusinessValidationMessage('Warning msg', MessageLevel.WARNING),
            ])

    def _first_business_validation(self):
        return False

    def _other_business_validation(self):
        return False


class TestBusinessValidator(SimpleTestCase):

    def test_property_messages(self):
        validator = ValidatorTest()
        expected_result = [
            BusinessValidationMessage("Error message", MessageLevel.ERROR),
            BusinessValidationMessage('Warning msg', MessageLevel.WARNING),
        ]
        validator.is_valid()
        self.assertEqual(validator.messages, expected_result)
        success_message = ValidatorTest.success_messages[0]
        self.assertNotIn(success_message, validator.messages)

    def test_property_messages_when_no_success_messages_set(self):
        validator = ValidatorTest()
        validator.success_messages = None
        expected_result = [
            BusinessValidationMessage("Error message", MessageLevel.ERROR),
            BusinessValidationMessage('Warning msg', MessageLevel.WARNING),
        ]
        validator.is_valid()
        self.assertEqual(validator.messages, expected_result)

    def test_property_error_message(self):
        validator = ValidatorTest()
        expected_result = [
            BusinessValidationMessage("Error message", MessageLevel.ERROR),
        ]
        validator.is_valid()
        self.assertEqual(validator.error_messages, expected_result)

    def test_property_warning_messages(self):
        validator = ValidatorTest()
        expected_result = [
            BusinessValidationMessage('Warning msg', MessageLevel.WARNING),
        ]
        validator.is_valid()
        self.assertEqual(validator.warning_messages, expected_result)

    def test_is_valid(self):
        validator = ValidatorTest()
        self.assertFalse(validator.is_valid())

    def test_is_valid_called_twice_on_same_instance(self):
        validator = ValidatorTest()
        self.assertFalse(validator.is_valid())
        self.assertFalse(validator.is_valid())  # Called a second time
        expected_result = [
            BusinessValidationMessage("Error message", MessageLevel.ERROR),
            BusinessValidationMessage('Warning msg', MessageLevel.WARNING),
        ]
        self.assertNotIn("Success msg", validator.messages, "Should only return warnings and success when is valid")
        self.assertEqual(validator.messages, expected_result, "Assert the validator doesn't add messages twice")

    def test_reset_messages_does_not_reset_success_message(self):
        validator = ValidatorTest()
        initial_success_messages = list(validator.success_messages)
        validator._reset_messages()
        self.assertListEqual(
            validator.success_messages,
            initial_success_messages,
            "Success message is an attribute of the class ; it is a static value, it can't be removed."
        )

    def test_success_message_to_add_should_be_ignored(self):
        validator = ValidatorTest()
        validator.add_message(BusinessValidationMessage("Success", MessageLevel.SUCCESS))
        self.assertNotIn("Success", validator.messages)

    def test_add_message_when_arg_is_not_success_message(self):
        validator = ValidatorTest()
        validator.add_message(BusinessValidationMessage("A message", MessageLevel.WARNING))
        self.assertIn("A message", validator.messages)

    def test_add_error_message(self):
        validator = ValidatorTest()
        validator.add_error_message("An error message")
        self.assertIn("An error message", validator.messages)

    def test_add_success_message(self):
        validator = ValidatorTest()
        validator.add_success_message("test")
        self.assertIn("test", validator.success_messages)

    def test_add_warning_message(self):
        validator = ValidatorTest()
        validator.add_warning_message("warning msg test")
        self.assertIn("warning msg test", validator.warning_messages)


class TestBusinessValidationMessageList(SimpleTestCase):

    def setUp(self):
        self.error_message = BusinessValidationMessage("error message", MessageLevel.ERROR)
        self.warning_message = BusinessValidationMessage("warning message", MessageLevel.WARNING)
        self.success_message = BusinessValidationMessage("success message", MessageLevel.SUCCESS)
        self.messages = [
            self.error_message,
            self.warning_message,
            self.success_message,
        ]

    def test_contains_error_when_has_error(self):
        message_list = BusinessValidationMessageList(messages=[self.error_message])
        self.assertTrue(message_list.contains_errors())

    def test_contains_error_when_has_warning(self):
        message_list = BusinessValidationMessageList(messages=[self.warning_message])
        self.assertFalse(message_list.contains_errors())

    def test_contains_error_when_messages_is_empty(self):
        message_list = BusinessValidationMessageList(messages=[])
        self.assertFalse(message_list.contains_errors())

    def test_errors_property(self):
        message_list = BusinessValidationMessageList(messages=self.messages)
        self.assertListEqual(message_list.errors, [self.error_message])

    def test_warnings_property(self):
        message_list = BusinessValidationMessageList(messages=self.messages)
        self.assertListEqual(message_list.warnings, [self.warning_message])

    def test_success_property(self):
        message_list = BusinessValidationMessageList(messages=self.messages)
        self.assertListEqual(message_list.success, [self.success_message])
