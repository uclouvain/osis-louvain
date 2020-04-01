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
from typing import List
from unittest.mock import PropertyMock, patch

from base.ddd.utils.validation_message import MessageLevel, BusinessValidationMessage


class ValidatorPatcherMixin:

    def mock_validator(self, validator_to_patch, messages: List[str], level: MessageLevel = MessageLevel.ERROR):
        """
        Mixin used to mock the "messages" attribute of the validator passed in parameter.
        It aims to avoid too many decorators "@patch" above the tests methods.
        :param validator_to_patch: a BusinessValidator class
        :param messages: Messages returned by the validator (mock the 'messages' attribute of the validator)
        :param level: The severity level of the messages
        :return: -
        """
        assert validator_to_patch, "mandatory arg"
        assert messages is not None, "mandatory arg"
        if not messages:
            messages = []

        patcher_validate = patch.object(validator_to_patch, 'validate', auto_spec=True)
        self.addCleanup(patcher_validate.stop)
        patcher_validate.start()

        patcher_messages = patch.object(
            validator_to_patch,
            'messages',
            new_callable=PropertyMock,
            return_value=[BusinessValidationMessage(msg, level) for msg in messages]
        )
        self.addCleanup(patcher_messages.stop)
        patcher_messages.start()
