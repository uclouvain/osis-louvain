##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, Callable, List

from ddd.logic.learning_unit.commands import CreateLearningUnitCommand
from ddd.logic.learning_unit.use_case.write.create_learning_unit_service import create_learning_unit
from ddd.logic.shared_kernel.academic_year.commands import SearchAcademicYearCommand
from ddd.logic.shared_kernel.academic_year.use_case.read.search_academic_years_service import search_academic_years
from ddd.logic.shared_kernel.language.commands import SearchLanguagesCommand
from ddd.logic.shared_kernel.language.use_case.read.search_languages_service import search_languages
from education_group.ddd.command import PostponeCertificateAimsCommand
from education_group.ddd.repository.group import GroupRepository
from education_group.ddd.repository.mini_training import MiniTrainingRepository
from education_group.ddd.repository.training import TrainingRepository
from education_group.ddd.service.write.postpone_certificate_aims_modification_service import \
    postpone_certificate_aims_modification
from infrastructure.learning_unit.repository.entity_repository import UclEntityRepository
from infrastructure.learning_unit.repository.learning_unit import LearningUnitRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.shared_kernel.language.repository.language import LanguageRepository
from osis_common.ddd.interface import CommandRequest, ApplicationServiceResult
from program_management.ddd.command import PostponeTrainingAndRootGroupModificationWithProgramTreeCommand, \
    PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand, UpdateAndPostponeRootGroupCommand
from program_management.ddd.service.write.postpone_mini_training_and_program_tree_modifications_service import \
    postpone_mini_training_and_program_tree_modifications
from program_management.ddd.service.write.postpone_training_and_program_tree_modifications_service import \
    postpone_training_and_program_tree_modifications
from program_management.ddd.service.write.update_and_postpone_root_group_service import update_and_postpone_root_group


class MessageBus:
    command_handlers = {
        CreateLearningUnitCommand: lambda cmd: create_learning_unit(
            cmd, LearningUnitRepository(), UclEntityRepository()
        ),
        SearchLanguagesCommand: lambda cmd: search_languages(cmd, LanguageRepository()),
        SearchAcademicYearCommand: lambda cmd: search_academic_years(cmd, AcademicYearRepository()),
        PostponeTrainingAndRootGroupModificationWithProgramTreeCommand:
            lambda cmd: postpone_training_and_program_tree_modifications(
                cmd, AcademicYearRepository(), TrainingRepository()
            ),
        PostponeMiniTrainingAndRootGroupModificationWithProgramTreeCommand:
            lambda cmd: postpone_mini_training_and_program_tree_modifications(
                cmd, AcademicYearRepository(), MiniTrainingRepository()
            ),
        UpdateAndPostponeRootGroupCommand: lambda cmd: update_and_postpone_root_group(
            cmd, AcademicYearRepository(), GroupRepository()
        ),
        PostponeCertificateAimsCommand: lambda cmd: postpone_certificate_aims_modification(
            cmd, AcademicYearRepository()
        )
    }  # type: Dict[CommandRequest, Callable[[CommandRequest], ApplicationServiceResult]]

    def invoke(self, command: CommandRequest) -> ApplicationServiceResult:
        return self.command_handlers[command.__class__](command)

    def invoke_multiple(self, commands: List['CommandRequest']) -> List[ApplicationServiceResult]:
        return [self.invoke(command) for command in commands]


message_bus_instance = MessageBus()
