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
from typing import TYPE_CHECKING

# FIXME :: Temporary solution ; waiting for update python to 3.8 for data structure

if TYPE_CHECKING:
    from program_management.ddd.domain.node import Node, NodeEducationGroupYear, NodeLearningUnitYear, NodeGroupYear
    from program_management.ddd.domain.program_tree import ProgramTree
    from program_management.ddd.domain.program_tree_version import ProgramTreeVersion, ProgramTreeVersionIdentity
    from program_management.ddd.domain.program_tree import Path
    from program_management.ddd.domain.link import Link
    from base.ddd.utils.validation_message import BusinessValidationMessage
    from program_management.ddd.domain.prerequisite import PrerequisiteExpression

    from program_management.ddd.repositories.load_tree import NodeKey
    from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository

    from program_management.ddd.command import CreateProgramTreeVersionCommand


FieldValueRepresentation = str  # Type used to verbose a field value for its view representation
