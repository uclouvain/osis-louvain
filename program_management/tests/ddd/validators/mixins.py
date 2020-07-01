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
from typing import List, Optional

import osis_common.ddd.interface
from base.ddd.utils import business_validator


class TestValidatorValidateMixin:
    def assertValidatorRaises(self, validator: business_validator.BusinessValidator, messages: Optional[List[str]]):
        with self.assertRaises(osis_common.ddd.interface.BusinessExceptions) as context_exc:
            validator.validate()

        if messages is not None:
            self.assertEqual(context_exc.exception.messages, messages)

    def assertValidatorNotRaises(self, validator: business_validator.BusinessValidator):
        try:
            validator.validate()
        except osis_common.ddd.interface.BusinessExceptions as exc:
            self.fail(
                "Validator {validator_name} raised unexpected BusinessException: {exception_message}".format(
                    validator_name=validator.__class__.__name__,
                    exception_message=str(exc.messages)
                )
            )
