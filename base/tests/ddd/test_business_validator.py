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
from base.ddd.utils.validation_message import BusinessValidationMessage, MessageLevel


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
            BusinessValidationMessage('Success msg', MessageLevel.SUCCESS)
        ]
        validator.is_valid()
        self.assertEqual(validator.messages, expected_result)

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
            BusinessValidationMessage('Success msg', MessageLevel.SUCCESS)
        ]
        self.assertEqual(validator.messages, expected_result, "Assert the validator doesn't add messages twice")

    def test_reset_messages_does_not_reset_success_message(self):
        validator = ValidatorTest()
        initial_success_message = validator.success_messages[0]
        validator._reset_messages()
        self.assertListEqual(
            validator.success_messages,
            [initial_success_message],
            "Success message is an attribute of the class ; it is a static value, it can't be removed."
        )

    def test_add_message_when_arg_is_success_message(self):
        validator = ValidatorTest()
        with self.assertRaises(AssertionError):
            validator.add_message(BusinessValidationMessage("Success", MessageLevel.SUCCESS))

    def test_add_message_when_arg_is_not_success_message(self):
        validator = ValidatorTest()
        validator.add_message(BusinessValidationMessage("A message", MessageLevel.WARNING))
        self.assertIn("A message", validator.messages)

    def test_add_error_message(self):
        validator = ValidatorTest()
        validator.add_error_message("An error message")
        self.assertIn("An error message", validator.messages)
