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


class CoorganizationIdentity(interface.EntityIdentity):
    def __init__(self, partner_name: str, training_acronym: str, training_year: int):
        self.partner_name = partner_name
        self.offer_acronym = training_acronym
        self.training_year = training_year

    def __eq__(self, other):
        return self.partner_name == other.partner_name and \
               self.offer_acronym == other.offer_acronym and \
               self.training_year == other.training_year

    def __hash__(self):
        return hash(self.partner_name + self.offer_acronym + str(self.training_year))


class Coorganization(interface.Entity):
    def __init__(
            self,
            entity_id: CoorganizationIdentity,
            partner: AcademicPartner,
            is_for_all_students: bool = False,
            is_reference_institution: bool = False,
            certificate_type: DiplomaCoorganizationTypes = DiplomaCoorganizationTypes.NOT_CONCERNED,
            is_producing_certificate: bool = False,
            is_producing_certificate_annexes: bool = False
    ):
        super(Coorganization, self).__init__(entity_id=entity_id)
        self.entity_id = entity_id
        self.partner = partner
        self.is_for_all_students = is_for_all_students or False
        self.is_reference_institution = is_reference_institution or False
        self.certificate_type = certificate_type or DiplomaCoorganizationTypes.NOT_CONCERNED
        self.is_producing_certificate = is_producing_certificate or False
        self.is_producing_certificate_annexes = is_producing_certificate_annexes or False
