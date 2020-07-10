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
import operator

import factory.fuzzy

from cms.enums import entity_name


class TextLabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "cms.TextLabel"

    parent = None
    entity = factory.Iterator(entity_name.ENTITY_NAME, getter=operator.itemgetter(0))
    label = factory.fuzzy.FuzzyText(prefix="Label ", length=20)
    order = factory.fuzzy.FuzzyInteger(1, 10)
    published = factory.Iterator([True, False])


class OfferTextLabelFactory(TextLabelFactory):
    entity = entity_name.OFFER_YEAR


class GroupTextLabelFactory(TextLabelFactory):
    entity = entity_name.GROUP_YEAR


class LearningUnitYearTextLabelFactory(TextLabelFactory):
    entity = entity_name.LEARNING_UNIT_YEAR
