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
from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from program_management.ddd.business_types import *

AUTHORIZED_TYPES = (set(MiniTrainingType) | set(TrainingType)) - set(TrainingType.finality_types_enum()) \
                   - {MiniTrainingType.OPTION, MiniTrainingType.MOBILITY_PARTNERSHIP}


class AuthorizedRootTypeForPrerequisite(BusinessValidator):
    def __init__(self, root_node: 'Node'):
        super().__init__()

        self.root_node = root_node

    def validate(self):
        if self.root_node.node_type not in AUTHORIZED_TYPES:
            self.add_error_message(
                _("You must be in the context of a training to modify the prerequisites of a learning unit "
                  "(current context: %(title)s)") % {
                    'title': str(self.root_node)
                }
            )
