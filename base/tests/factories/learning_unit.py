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
import datetime
import string

import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from base.business.learning_units import edition
from base.models.enums import learning_container_year_types, learning_unit_year_subtypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_unit_year import LearningUnitYearWithComponentsFactory

fake = Faker()


class LearningUnitFactory(DjangoModelFactory):
    class Meta:
        model = "base.LearningUnit"

    learning_container = factory.SubFactory(LearningContainerFactory)
    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1), datetime.datetime(2017, 3, 1))
    start_year = factory.SubFactory(AcademicYearFactory, year=factory.fuzzy.FuzzyInteger(2000, timezone.now().year))
    end_year = None
    faculty_remark = factory.fuzzy.FuzzyText(length=255)
    other_remark = factory.fuzzy.FuzzyText(length=255)


class LearningUnitFactoryWithAnnualizedData(LearningUnitFactory):

    @factory.post_generation
    def learningunityears(obj, create, extracted, **kwargs):
        academic_years = kwargs.pop("academic_years")
        start_year, *following_years = academic_years

        initial_learning_unit_year = LearningUnitYearWithComponentsFactory(
            academic_year=start_year,
            learning_unit=obj,
            subtype=learning_unit_year_subtypes.FULL,
            **kwargs
        )

        for acy in following_years:
            edition.duplicate_learning_unit_year(initial_learning_unit_year, acy)
