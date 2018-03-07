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
from django.core.exceptions import PermissionDenied

from base.models.entity import Entity
from base.models.enums import offer_year_entity_type
from base.models.person import Person
from base.models.program_manager import is_program_manager
from base.models import person_entity


def can_user_edit_administrative_data(a_user, an_education_group_year):
    """
    Edition of administrative data is allowed for user which have permission AND
            if CENTRAL_MANAGER: Check attached entities [person_entity]
            else Check if user is program manager of education group
    """
    if not a_user.has_perm("base.can_edit_education_group_administrative_data"):
        return False

    person = Person.objects.get(user=a_user)
    if person.is_central_manager() and _is_management_entity_linked_to_user(person, an_education_group_year):
        return True

    return is_program_manager(a_user, education_group=an_education_group_year.education_group)


def _is_management_entity_linked_to_user(person, an_education_group_year):
    entities = Entity.objects.filter(offeryearentity__education_group_year=an_education_group_year,
                                     offeryearentity__type=offer_year_entity_type.ENTITY_MANAGEMENT)

    return person_entity.is_attached_entities(person, entities)


def assert_category_of_education_group_year(education_group_year, authorized_categories):
    if education_group_year.education_group_type.category not in authorized_categories:
        raise PermissionDenied("Education group category is not correct.")
