##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ObjectDoesNotExist

from base.models import person_entity
from base.models.entity_version import EntityVersion
from base.models.person_entity import PersonEntity
from base.models.entity_container_year import EntityContainerYear

MAP_ENTITY_FIELD = {
    EntityVersion: 'entity',
    PersonEntity: 'entity',
    EntityContainerYear: 'entity'
}


def filter_by_attached_entities(person, entity_queryset):

    entities_attached = person_entity.find_entities_by_person(person)
    field_path = MAP_ENTITY_FIELD.get(entity_queryset.model)
    if not field_path:
        raise ObjectDoesNotExist
    field_filter = "{}__in".format(field_path)
    return entity_queryset.filter(**{field_filter: entities_attached})
