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

from base.models.entity import Entity
from base.models.person import Person
from education_group.auth.scope import Scope
from osis_role import role
from osis_role.contrib.models import EntityRoleModel


class EntityRoleHelper():
    """
       Utility class to provide role-related static methods
    """
    @staticmethod
    def get_all_entities(person: Person, group_names: List[str]) -> List[Entity]:
        role_mdls = [
            r for r in role.role_manager.roles if issubclass(r, EntityRoleModel) and r.group_name in group_names
        ]
        qs = None

        for role_mdl in role_mdls:
            subqs = role_mdl.objects.filter(person=person)
            if hasattr(role_mdl, 'scopes'):
                subqs = subqs.filter(scopes=[Scope.ALL.value])
            subqs = subqs.values('entity_id', 'with_child')
            if qs is None:
                qs = subqs
            else:
                qs = qs.union(subqs)

        return qs.get_entities_ids() if qs else Entity.objects.none()
