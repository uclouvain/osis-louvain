##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

VOLUME_TOTAL = 'VOLUME_TOTAL'
VOLUME_Q1 = 'VOLUME_Q1'
VOLUME_Q2 = 'VOLUME_Q2'
PLANNED_CLASSES = 'PLANNED_CLASSES'
VOLUME_REQUIREMENT_ENTITY = 'VOLUME_REQUIREMENT_ENTITY'
VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1 = 'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1'
VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2 = 'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2'
VOLUME_TOTAL_REQUIREMENT_ENTITIES = 'VOLUME_TOTAL_REQUIREMENT_ENTITIES'
REAL_CLASSES = 'REAL_CLASSES'
VOLUME_GLOBAL = 'VOLUME_GLOBAL'

COMPONENT_DETAILS = {
    VOLUME_TOTAL: _('Vol. annual'),
    VOLUME_Q1: _('Vol. Q1'),
    VOLUME_Q2: _('Vol. Q2'),
    PLANNED_CLASSES: _('Planned classes'),
    VOLUME_REQUIREMENT_ENTITY: _('volume requirement entity'),
    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: _('volume additional requirement entity 1'),
    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: _('volume additional requirement entity 2'),
    VOLUME_TOTAL_REQUIREMENT_ENTITIES: _('volume total requirement entities'),
    REAL_CLASSES: _('Real classes'),
    VOLUME_GLOBAL: _('Vol. global'),
}
