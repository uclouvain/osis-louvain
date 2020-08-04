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
from typing import Union

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from osis_common.ddd import interface


class EducationGroupTypeConverter(interface.DomainService):

    @classmethod
    def convert_type_str_to_enum(cls, type: str) -> Union[TrainingType, MiniTrainingType, GroupType]:
        if type in GroupType.get_names():
            return GroupType[type]
        elif type in TrainingType.get_names():
            return TrainingType[type]
        elif type in MiniTrainingType.get_names():
            return MiniTrainingType[type]
        raise interface.BusinessException('Unsupported group type')
