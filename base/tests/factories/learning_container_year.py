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
import operator

import factory.fuzzy

from base.models.enums import learning_container_year_types
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.learning_container import LearningContainerFactory


class LearningContainerYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.LearningContainerYear"

    external_id = factory.Sequence(lambda n: '10000000%02d' % n)
    academic_year = factory.SubFactory(AcademicYearFactory)
    learning_container = factory.SubFactory(LearningContainerFactory)
    container_type = factory.Iterator(learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL,
                                      getter=operator.itemgetter(0))
    common_title = factory.Sequence(lambda n: 'Learning container year - %d' % n)
    common_title_english = factory.Sequence(lambda n: 'Learning container year english - %d' % n)
    acronym = factory.Sequence(lambda n: 'LCY-%d' % n)

    changed = factory.fuzzy.FuzzyNaiveDateTime(
        datetime.datetime(2016, 1, 1),
        datetime.datetime(2017, 3, 1)
    )

    in_charge = False
    type_declaration_vacant = None

    requirement_entity = factory.SubFactory(EntityFactory)
    allocation_entity = factory.LazyAttribute(lambda o: o.requirement_entity)
    additional_entity_1 = None
    additional_entity_2 = None
