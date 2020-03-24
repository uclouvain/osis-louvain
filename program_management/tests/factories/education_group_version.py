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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import string
from datetime import datetime

import factory.fuzzy
from dateutil.relativedelta import relativedelta

from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.tests.factories.group_year import GroupYearFactory


class EducationGroupVersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'program_management.EducationGroupVersion'

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.today() - relativedelta(years=1), datetime.today())

    is_transition = False
    version_name = factory.fuzzy.FuzzyText(length=10)
    root_group = factory.SubFactory(GroupYearFactory)
    offer = factory.SubFactory(EducationGroupYearFactory)
    title_fr = factory.fuzzy.FuzzyText(length=15)
    title_en = factory.fuzzy.FuzzyText(length=15)


class StandardEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = ''


class StandardTransitionEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = ''
    is_transition = True


class ParticularTransitionEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = 'CEMS'
    is_transition = True
