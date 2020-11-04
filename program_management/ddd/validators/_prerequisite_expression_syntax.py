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

from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.domain import prerequisite


class PrerequisiteExpressionSyntaxValidator(BusinessValidator):

    def __init__(self, prerequisite_string: prerequisite.PrerequisiteExpression, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prerequisite_string = prerequisite_string

    def validate(self, *args, **kwargs):
        if not re.match(prerequisite.PREREQUISITE_SYNTAX_REGEX, self.prerequisite_string):
            self.add_error_message(_("Prerequisites are invalid"))
