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
from education_group.ddd import command
from education_group.ddd.domain import mini_training
from education_group.ddd.repository import mini_training as mini_training_repository
from education_group.ddd.validators.validators_by_business_action import DeleteOrphanMiniTrainingValidatorList


def delete_orphan_mini_training(cmd: command.DeleteOrphanMiniTrainingCommand) -> 'mini_training.MiniTrainingIdentity':
    mini_training_identity = mini_training.MiniTrainingIdentity(acronym=cmd.abbreviated_title, year=cmd.year)
    mini_training_to_delete = mini_training_repository.MiniTrainingRepository.get(mini_training_identity)

    DeleteOrphanMiniTrainingValidatorList(mini_training_to_delete).validate()

    mini_training_repository.MiniTrainingRepository.delete(mini_training_identity)

    return mini_training_identity
