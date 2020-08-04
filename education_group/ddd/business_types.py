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
    from education_group.ddd.domain.training import Training, TrainingIdentity
    from education_group.ddd.domain.group import Group, GroupIdentity
    from education_group.ddd.domain.mini_training import MiniTraining, MiniTrainingIdentity
    from education_group.ddd.command import CreateTrainingCommand
    from education_group.ddd.domain._study_domain import StudyDomainIdentity
    from education_group.ddd.domain._campus import Campus
    from education_group.ddd.domain._co_organization import CoorganizationIdentity
    from education_group.ddd.domain._diploma import DiplomaAimIdentity
    from education_group.ddd.repository.training import TrainingRepository
    from education_group.ddd.repository.mini_training import MiniTrainingRepository
