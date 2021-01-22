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

from program_management.ddd.business_types import *
from django.utils.translation import gettext_lazy as _

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.domain import prerequisite


class PrerequisiteItemsValidator(BusinessValidator):
    def __init__(
            self,
            prerequisite_string: 'PrerequisiteExpression',
            node: 'NodeLearningUnitYear',
            program_tree: 'ProgramTree'
    ):
        super().__init__()
        self.prerequisite_string = prerequisite_string
        self.node = node
        self.program_tree = program_tree
        self.codes_permitted = {n.code for n in self.program_tree.get_nodes_permitted_as_prerequisite()}

    def validate(self, *args, **kwargs):
        node_not_in_codes_permitted = self.node.code not in self.codes_permitted
        if self.program_tree.is_used_only_inside_minor_or_deepening(self.node) and node_not_in_codes_permitted:
            minor_or_deepening = [
                n.full_acronym() for n in self.program_tree.search_indirect_parents(self.node)
                if n.is_minor_or_deepening()
            ]
            self.add_error_message(
                _("The learning unit %(acronym)s is used inside %(mini_trainings)s but not inside %(training)s") % {
                    'acronym': self.node.code,
                    'mini_trainings': ','.join(minor_or_deepening),
                    'training': self.program_tree.root_node.full_acronym(),
                }
            )
        codes_used_in_prerequisite_string = self._extract_acronyms()
        codes_used_but_not_permitted = set(codes_used_in_prerequisite_string) - set(self.codes_permitted)
        if codes_used_but_not_permitted:
            for code in sorted(codes_used_but_not_permitted):
                self.add_error_message(
                    _("The learning unit %(acronym)s is not contained inside the formation") % {'acronym': code}
                )

            self.add_warning_message(
                _("The prerequisites %(prerequisites)s for the learning unit %(learning_unit)s "
                  "are not inside the selected training %(root)s") % {
                    "prerequisites": ", ".join(codes_used_but_not_permitted),
                    "learning_unit": self.node,
                    "root": self.program_tree.root_node,
                }
            )

        if self.node.code in codes_used_in_prerequisite_string:
            self.add_error_message(
                _("A learning unit cannot be prerequisite to itself : %(acronym)s") % {'acronym': self.node.code}
            )

    def _extract_acronyms(self):
        return re.findall(prerequisite.ACRONYM_REGEX, self.prerequisite_string)
