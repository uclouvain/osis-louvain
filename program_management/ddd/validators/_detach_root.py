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

from django.utils.translation import gettext_lazy as _

import osis_common.ddd.interface
from base.ddd.utils import business_validator
from program_management.ddd.business_types import *


class DetachRootValidator(business_validator.BusinessValidator):

    def __init__(self, tree: 'ProgramTree', path_to_detach: 'Path'):
        super(DetachRootValidator, self).__init__()
        self.path_to_detach = path_to_detach
        self.tree = tree

    def validate(self):
        if self.tree.is_root(self.tree.get_node(self.path_to_detach)):
            raise osis_common.ddd.interface.BusinessExceptions([_("Cannot perform detach action on root.")])
