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
from enum import Enum
from typing import List


class MessageLevel(Enum):
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    SUCCESS = "succes"


class BusinessValidationMessage:
    message = None
    level = MessageLevel.ERROR

    def __init__(self, message: str, level: MessageLevel = None):
        self.message = message
        self.level = level

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.message
        return other.message == self.message

    def __str__(self):
        return "%(level)s %(msg)s" % {'level': self.level, 'msg': self.message}

    def is_error(self):
        return self.level == MessageLevel.ERROR

    def is_success(self):
        return self.level == MessageLevel.SUCCESS

    def is_warning(self):
        return self.level == MessageLevel.WARNING

    @staticmethod
    def contains_errors(messages: List['BusinessValidationMessage']) -> bool:
        return any(msg.is_error() for msg in messages)
