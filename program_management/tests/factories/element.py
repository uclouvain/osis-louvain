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

from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from education_group.tests.factories.group_year import GroupYearFactory
from learning_unit.tests.factories.learning_class_year import LearningClassYearFactory


class ElementFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'program_management.Element'
        django_get_or_create = ('group_year', 'learning_unit_year', 'learning_class_year')

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1), datetime.datetime(2017, 3, 1))

    group_year = None
    learning_unit_year = None
    learning_class_year = None


class ElementGroupYearFactory(ElementFactory):
    group_year = factory.SubFactory(GroupYearFactory)


class ElementLearningUnitYearFactory(ElementFactory):
    learning_unit_year = factory.SubFactory(LearningUnitYearFactory)


class ElementLearningClassYearFactory(ElementFactory):
    learning_class_year = factory.SubFactory(LearningClassYearFactory)
