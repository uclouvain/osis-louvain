##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import Decimal

import attr

from base.models.enums.quadrimesters import DerogationQuadrimester
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class Duration(interface.ValueObject):
    hours = attr.ib(type=int)
    minutes = attr.ib(type=int)

    @property
    def quantity_in_hours(self) -> Decimal:
        minutes_in_1_hour = 60
        minutes_from_hours = self.hours * minutes_in_1_hour
        total_minutes = minutes_from_hours + self.minutes
        number_of_decimals = 2
        return round(Decimal(total_minutes / minutes_in_1_hour), number_of_decimals)


@attr.s(frozen=True, slots=True)
class Volumes(interface.ValueObject):
    volume_first_quadrimester = attr.ib(type=Duration)
    volume_second_quadrimester = attr.ib(type=Duration)
    volume_annual = attr.ib(type=Duration)
    derogation_quadrimester = attr.ib(type=DerogationQuadrimester)


@attr.s(frozen=True, slots=True)
class LecturingPart(interface.ValueObject):
    acronym = 'PM'
    volumes = attr.ib(type=Volumes)


@attr.s(frozen=True, slots=True)
class PracticalPart(interface.ValueObject):
    acronym = 'PP'
    volumes = attr.ib(type=Volumes)
