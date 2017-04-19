##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import factory
import factory.fuzzy
import string
import operator
from django.conf import settings
from django.utils import timezone
from base.enums import structure_type


def _get_tzinfo():
    if settings.USE_TZ:
        return timezone.get_current_timezone()
    else:
        return None


class StructureFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.Structure'
        #abstract = False

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=_get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=_get_tzinfo()))

    acronym = acronym = factory.Sequence(lambda n: 'ACR-%d' % n)
    title = factory.Sequence(lambda n: 'TITLE-%d' % n)
    #part_of = factory.SubFactory(Structure)
    #part_of = factory.SubFactory('osis.base.tests.factories.Structure')
    #part_of = factory.SubFactory('base.tests.factories.StructureFactory')
    # part_of = factory.SubFactory('base.Structure')
    #part_of = factory.SubFactory('self')
    #part_of = factory.SubFactory('base.tests.factories.Structure')
    # part_of = factory.SubFactory(StructureFactory)
    #part_of = factory.SubFactory('base.models.structure')
    type = factory.Iterator(structure_type.TYPES, getter=operator.itemgetter(0))