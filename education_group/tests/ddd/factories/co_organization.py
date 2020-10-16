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
import factory.fuzzy

from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from education_group.ddd.domain._co_organization import Coorganization, CoorganizationIdentity
from education_group.tests.ddd.factories.academic_partner import AcademicPartnerFactory


class CoorganizationIdentityFactory(factory.Factory):
    class Meta:
        model = CoorganizationIdentity
        abstract = False

    partner_name = factory.Sequence(lambda n: 'PARTNER_%02d' % n)
    training_acronym = factory.Sequence(lambda n: 'OFFER_%02d' % n)
    training_year = factory.fuzzy.FuzzyInteger(1999, 2099)


class CoorganizationFactory(factory.Factory):
    class Meta:
        model = Coorganization
        abstract = False

    entity_id = factory.SubFactory(CoorganizationIdentityFactory)
    partner = factory.SubFactory(AcademicPartnerFactory)
    is_for_all_students = False
    is_reference_institution = False
    certificate_type = DiplomaCoorganizationTypes.NOT_CONCERNED
    is_producing_certificate = False
    is_producing_certificate_annexes = False
