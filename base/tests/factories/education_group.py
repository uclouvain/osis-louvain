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
import string

import factory.fuzzy
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from base.business.education_groups import postponement
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from osis_common.utils.datetime import get_tzinfo

fake = Faker()


class EducationGroupFactory(DjangoModelFactory):
    class Meta:
        model = "base.EducationGroup"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = fake.date_time_this_decade(before_now=True, after_now=True, tzinfo=get_tzinfo())
    start_year = factory.SubFactory(AcademicYearFactory, year=factory.fuzzy.FuzzyInteger(2000, timezone.now().year))
    end_year = None


class EducationGroupWithAnnualizedDataDactory(EducationGroupFactory):

    @factory.post_generation
    def educationgroupyears(obj, create, extracted, **kwargs):
        academic_years = kwargs.pop("academic_years")
        start_year, *following_years = academic_years
        initial_education_group_year = EducationGroupYearFactory(
            education_group=obj,
            academic_year=start_year,
            **kwargs
        )
        for acy in following_years:
            postponement.duplicate_education_group_year(initial_education_group_year, acy)
