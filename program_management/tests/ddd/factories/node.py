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

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from program_management.ddd.domain.node import NodeEducationGroupYear, NodeLearningUnitYear, NodeGroupYear


def generate_end_date(node):
    return node.year + 10


class NodeFactory(factory.Factory):

    node_id = factory.Sequence(lambda n: n+1)
    code = factory.Sequence(lambda n: 'Code-%02d' % n)
    title = factory.Sequence(lambda n: 'Acronym-%02d' % n)
    year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)
    end_date = factory.LazyAttribute(generate_end_date)


class NodeEducationGroupYearFactory(NodeFactory):
    class Meta:
        model = NodeEducationGroupYear
        abstract = False

    node_type = factory.fuzzy.FuzzyChoice(TrainingType)
    offer_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_title_en = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_en = factory.fuzzy.FuzzyText(length=240)
    children = None


class NodeGroupYearFactory(NodeFactory):

    class Meta:
        model = NodeGroupYear
        abstract = False

    node_type = factory.fuzzy.FuzzyChoice(TrainingType)
    offer_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_title_en = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_en = factory.fuzzy.FuzzyText(length=240)
    children = None

    class Params:
        minitraining = factory.Trait(
            node_type=factory.fuzzy.FuzzyChoice(MiniTrainingType)
        )
        group = factory.Trait(
            node_type=factory.fuzzy.FuzzyChoice(GroupType)
        )


class NodeLearningUnitYearFactory(NodeFactory):

    class Meta:
        model = NodeLearningUnitYear
        abstract = False

    node_type = None
    is_prerequisite_of = []
    credits = factory.fuzzy.FuzzyDecimal(0, 10, precision=1)
