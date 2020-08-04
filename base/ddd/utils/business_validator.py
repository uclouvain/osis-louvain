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
from abc import ABC
from typing import List

from base.ddd.utils.validation_message import BusinessValidationMessage, MessageLevel


class BusinessValidator(ABC):

    _messages = None

    _validation_done = False

    success_messages = None

    def __init__(self, *args, **kwargs):
        self._messages = []
        if self.success_messages is None:
            self.success_messages = []
        self.success_messages = [
            BusinessValidationMessage(msg, MessageLevel.SUCCESS) if isinstance(msg, str) else msg
            for msg in self.success_messages
        ]

    @property
    def messages(self) -> List[BusinessValidationMessage]:
        """
        :return: All warnings and success messages if validator is valid.
        Return only errors and warnings if validator is not valid.
        """
        result = self._messages
        if not any(msg for msg in result if msg.is_error):
            result += self.success_messages or []
        return result

    @property
    def error_messages(self) -> List[BusinessValidationMessage]:
        return [msg for msg in self.messages if msg.level == MessageLevel.ERROR]

    @property
    def warning_messages(self) -> List[BusinessValidationMessage]:
        return [msg for msg in self.messages if msg.level == MessageLevel.WARNING]

    def is_valid(self) -> bool:
        if self._validation_done:
            self._reset_messages()
        self.validate()
        self._validation_done = True
        return not self.error_messages

    def add_message(self, msg: BusinessValidationMessage):
        if msg.level != MessageLevel.SUCCESS:
            self._messages.append(msg)

    def add_error_message(self, msg: str):
        self._messages.append(BusinessValidationMessage(msg, level=MessageLevel.ERROR))

    def add_success_message(self, msg: str):
        self.success_messages.append(
            BusinessValidationMessage(msg, level=MessageLevel.SUCCESS)
        )

    def add_warning_message(self, msg: str):
        self._messages.append(
            BusinessValidationMessage(msg, level=MessageLevel.WARNING)
        )

    def add_messages(self, messages: List[BusinessValidationMessage]):
        for msg in messages:
            self.add_message(msg)

    def validate(self, *args, **kwargs):
        """Method used to add messages during validation"""
        raise NotImplementedError()

    def _reset_messages(self):
        self._messages = []


class BusinessListValidator(BusinessValidator):
    validators = None

    def __init__(self):
        super(BusinessListValidator, self).__init__()

    def validate(self):
        for validator in self.validators:
            validator.validate()
            self.add_messages(validator.messages)
