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
import collections
from typing import List, Set, Iterable

from django.db.models import Subquery, OuterRef, Value, CharField

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from osis_role import role
from osis_role.contrib.models import EntityRoleModel

Row = collections.namedtuple("Row", ['group_name', 'person_id', 'entity_id', 'entity_recent_acronym'])


class EntityRoleHelper:
    """
       Utility class to provide role-related static methods
    """
    @staticmethod
    def get_all_entities(person: Person, group_names: Set[str], with_expired: bool = False) -> List[Entity]:
        role_mdls = [
            r for r in role.role_manager.roles if issubclass(r, EntityRoleModel) and r.group_name in group_names
        ]
        qs = None

        for role_mdl in role_mdls:
            subqs = role_mdl.objects.filter(person=person)
            subqs = subqs.values('entity_id', 'with_child')
            if qs is None:
                qs = subqs
            else:
                qs = qs.union(subqs)

        return qs.get_entities_ids(with_expired=with_expired) if qs else Entity.objects.none()

    @staticmethod
    def get_all_entities_for_persons(persons: Iterable[Person], group_names: Set[str]) -> Iterable[Row]:
        role_mdls = [
            r for r in role.role_manager.roles if issubclass(r, EntityRoleModel) and r.group_name in group_names
        ]

        qs = None
        for role_mdl in role_mdls:
            subqs = role_mdl.objects.filter(
                person__in=persons
            ).annotate(
                group_name=Value(role_mdl.group_name, output_field=CharField()),
                entity_recent_acronym=Subquery(
                    EntityVersion.objects.filter(
                        entity=OuterRef('entity__pk')
                    ).order_by('-start_date').values('acronym')[:1]
                )
            )
            subqs = subqs.values_list(*Row._fields)
            qs = subqs if qs is None else qs.union(subqs)

        if qs is None:
            return []

        return (Row._make(row) for row in qs.order_by("person_id", "group_name"))

    """
       Utility class to provide roles from a Person
    """
    @staticmethod
    def get_all_roles(person: Person) -> List[EntityRoleModel]:
        qs = []
        if not person:
            return qs

        role_mdls = [
            r for r in role.role_manager.roles if issubclass(r, EntityRoleModel)
        ]

        for role_mdl in role_mdls:
            for s in role_mdl.objects.filter(person=person):
                qs.append(type(s))
        return qs

    @classmethod
    def has_roles(cls, person: Person, role_cls_list: List['RoleModel']) -> bool:
        user_roles = cls.get_all_roles(person)
        return all(role_cls in user_roles for role_cls in role_cls_list)

    @classmethod
    def has_role(cls, person: Person, role_cls: 'RoleModel') -> bool:
        return cls.has_roles(person, [role_cls])
