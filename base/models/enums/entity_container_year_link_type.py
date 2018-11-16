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
from django.utils.translation import ugettext_lazy as _

from base.models.utils.utils import ChoiceEnum

REQUIREMENT_ENTITY = "REQUIREMENT_ENTITY"
ALLOCATION_ENTITY = "ALLOCATION_ENTITY"
ADDITIONAL_REQUIREMENT_ENTITY_1 = "ADDITIONAL_REQUIREMENT_ENTITY_1"
ADDITIONAL_REQUIREMENT_ENTITY_2 = "ADDITIONAL_REQUIREMENT_ENTITY_2"

ENTITY_TYPE_LIST = [
    REQUIREMENT_ENTITY,
    ALLOCATION_ENTITY,
    ADDITIONAL_REQUIREMENT_ENTITY_1,
    ADDITIONAL_REQUIREMENT_ENTITY_2
]


class EntityContainerYearLinkTypes(ChoiceEnum):
    REQUIREMENT_ENTITY = _("Requirement entity")
    ALLOCATION_ENTITY = _("Allocation entity")
    ADDITIONAL_REQUIREMENT_ENTITY_1 = _("Additional requirement entity 1")
    ADDITIONAL_REQUIREMENT_ENTITY_2 = _("Additional requirement entity 2")


REQUIREMENT_ENTITIES = [
    REQUIREMENT_ENTITY,
    ADDITIONAL_REQUIREMENT_ENTITY_1,
    ADDITIONAL_REQUIREMENT_ENTITY_2
]
