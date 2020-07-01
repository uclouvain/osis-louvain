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
from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from education_group.ddd.domain._academic_partner import AcademicPartner
from osis_common.ddd import interface


class Coorganization(interface.ValueObject):
    def __init__(
            self,
            partner: AcademicPartner,
            is_for_all_students: bool = False,
            is_reference_institution: bool = False,
            certificate_type: DiplomaCoorganizationTypes = DiplomaCoorganizationTypes.NOT_CONCERNED,
            is_producing_certificate: bool = False,
            is_producing_certificate_annexes: bool = False
    ):
        self.partner = partner
        self.is_for_all_students = is_for_all_students or False
        self.is_reference_institution = is_reference_institution or False
        self.certificate_type = certificate_type or DiplomaCoorganizationTypes.NOT_CONCERNED
        self.is_producing_certificate = is_producing_certificate or False
        self.is_producing_certificate_annexes = is_producing_certificate_annexes or False

    def __eq__(self, other):
        return self.partner == other.partner and \
            self.is_for_all_students == other.is_for_all_students and \
            self.is_reference_institution == other.is_reference_institution and \
            self.certificate_type == other.certificate_type and \
            self.is_producing_certificate == other.is_producing_certificate and \
            self.is_producing_certificate_annexes == other.is_producing_certificate_annexes

    def __hash__(self):
        return hash(
            str(self.partner) +
            str(self.is_for_all_students) +
            str(self.is_reference_institution) +
            self.certificate_type.name +
            str(self.is_producing_certificate) +
            str(self.is_producing_certificate_annexes)
        )
