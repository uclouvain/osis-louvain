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
import re
from typing import Optional

from django.utils.translation import gettext_lazy as _
from base.ddd.utils.business_validator import BusinessValidator

BLOCK_MAX_AUTHORIZED_VALUE = 6


class BlockValidator(BusinessValidator):
    def __init__(self, block: Optional[int]):
        super().__init__()
        self.block = block

    def validate(self, *args, **kwargs):
        if self.block is None:
            return

        block_regex = r"1?2?3?4?5?6?"
        match_result = re.fullmatch(block_regex, str(self.block))

        if not match_result:
            error_msg = _(
                "Please register a maximum of %(max_authorized_value)s digits in ascending order, "
                "without any duplication. Authorized values are from 1 to 6. Examples: 12, 23, 46"
            ) % {'max_authorized_value': BLOCK_MAX_AUTHORIZED_VALUE}
            self.add_error_message(error_msg)
