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

from django.db import transaction

from education_group.ddd.business_types import *
from program_management.ddd import command as pgm_command
from program_management.ddd.service.write import paste_element_service, create_training_with_program_tree


@transaction.atomic()
def create_and_attach_training(
        create_and_attach_cmd: pgm_command.CreateAndAttachTrainingCommand
) -> List['TrainingIdentity']:

    # GIVEN
    # Nothing (later, should contains permissions or access rights)

    # WHEN
    training_ids = create_training_with_program_tree.create_and_report_training_with_program_tree(create_and_attach_cmd)

    # THEN
    paste_element_service.paste_element(__convert_to_paste_element_cmd(create_and_attach_cmd))
    return training_ids


def __convert_to_paste_element_cmd(
        create_and_attach_training: pgm_command.CreateAndAttachTrainingCommand
) -> pgm_command.PasteElementCommand:
    return pgm_command.PasteElementCommand(
        node_to_paste_code=create_and_attach_training.code,
        node_to_paste_year=create_and_attach_training.year,
        path_where_to_paste=create_and_attach_training.path_to_paste,
    )
