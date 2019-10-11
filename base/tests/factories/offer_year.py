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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import factory.fuzzy

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.offer_type import OfferTypeFactory
from base.tests.factories.structure import StructureFactory


class OfferYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.OfferYear"
        exclude = ("corresponding_education_group_year",)

    offer = factory.SubFactory(OfferFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    acronym = factory.Sequence(lambda n: 'Offer %d' % n)
    title = factory.LazyAttribute(lambda obj: '{obj.academic_year} {obj.acronym}'.format(obj=obj).lower())
    entity_management = factory.SubFactory(StructureFactory)
    entity_administration_fac = factory.SubFactory(StructureFactory)
    offer_type = factory.SubFactory(OfferTypeFactory)

    corresponding_education_group_year = factory.SubFactory(
        EducationGroupYearFactory,
        academic_year=factory.SelfAttribute("..academic_year"),
        acronym=factory.SelfAttribute("..acronym")
    )
