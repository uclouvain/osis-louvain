##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.utils.translation import gettext_lazy as _

from program_management.ddd.domain.node import NodeLearningUnitYear
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.validators.validators_by_business_action import UpdatePrerequisiteValidatorList


class PrerequisiteForm(forms.Form):
    prerequisite_string = forms.CharField(
        label=_("Prerequisite"),
        required=False,
        help_text=_(
            "<b>Syntax rules</b>:<ul><li>No double parentheses.</li><li>Valid operators are OU or ET.</li><li>The "
            "operator must be the same inside all parentheses (groups).</li><li>The operator that linked groups must "
            "be different than the one that linked LU inside groups (parentheses).</li><li>The LU code cannot include "
            "spaces (ex: LDROI1001 and not LDROI&nbsp;1001).</li></ul></p><p><b>Examples</b>:<ul><li>A OU B OU C: "
            "valid</li><li>A ET B ET C : valid</li><li>A ET (B OU C) ET (D OU E): valid</li><li>A ET (B OU C) OU (D OU "
            "E): not valid</li><li>A ET (B ET C) ET (D ET E): not valid</li><li>A ET (B OU C) ET (D ET E): not valid"
            "</li></ul>"
        ),
    )

    def __init__(self, program_tree: ProgramTree, node: NodeLearningUnitYear, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.program_tree = program_tree
        self.node = node

    def clean_prerequisite_string(self):
        prerequisite_string = self.cleaned_data["prerequisite_string"]
        validator = UpdatePrerequisiteValidatorList(prerequisite_string, self.node, self.program_tree)
        if not validator.is_valid():
            for error_message in validator.error_messages:
                self.add_error("prerequisite_string", error_message.message)
        return prerequisite_string

    def save(self, commit=False):
        pass
