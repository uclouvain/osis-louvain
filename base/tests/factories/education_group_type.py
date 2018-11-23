##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator

import factory

from factory.django import DjangoModelFactory

from base.models.enums import education_group_categories, education_group_types


class EducationGroupTypeFactory(DjangoModelFactory):
    class Meta:
        model = "base.EducationGroupType"

    external_id = factory.Sequence(lambda n: '10000000%02d' % n)
    category = education_group_categories.TRAINING
    name = factory.Iterator(education_group_types.ALL_TYPES, getter=operator.itemgetter(0))


class ExistingEducationGroupTypeFactory(EducationGroupTypeFactory):
    class Meta:
        model = 'base.EducationGroupType'
        django_get_or_create = ('category', 'name')
