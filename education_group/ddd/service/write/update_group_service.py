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

from django.db import transaction

from base.models.enums.constraint_type import ConstraintTypeEnum
from education_group.ddd import command
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain._entity import Entity
from education_group.ddd.domain._remark import Remark
from education_group.ddd.domain._titles import Titles

from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.repository.group import GroupRepository


# TODO : Implement Validator (Actually in GroupFrom via ValidationRules)
@transaction.atomic()
def update_group(cmd: command.UpdateGroupCommand) -> 'GroupIdentity':
    group_identity = GroupIdentity(code=cmd.code, year=cmd.year)
    grp = GroupRepository.get(group_identity)

    grp.update(
        abbreviated_title=cmd.abbreviated_title,
        titles=Titles(title_fr=cmd.title_fr, title_en=cmd.title_en),
        credits=cmd.credits,
        content_constraint=ContentConstraint(
            type=ConstraintTypeEnum[cmd.constraint_type] if cmd.constraint_type else None,
            minimum=cmd.min_constraint,
            maximum=cmd.max_constraint
        ),
        management_entity=Entity(acronym=cmd.management_entity_acronym),
        teaching_campus=Campus(
            name=cmd.teaching_campus_name,
            university_name=cmd.organization_name
        ),
        remark=Remark(text_fr=cmd.remark_fr, text_en=cmd.remark_en)
    )
    return GroupRepository.update(grp)
