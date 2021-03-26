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
from base.models.enums.learning_container_year_types import LearningContainerYearType
from education_group.models.enums.constraint_type import ConstraintTypes
from program_management.ddd.domain.node import NodeLearningUnitYear, NodeGroupYear, Node, \
    NodeIdentity
from program_management.ddd.domain._campus import Campus
from program_management.ddd.domain.program_tree_version import STANDARD, NOT_A_TRANSITION
from program_management.models.enums.node_type import NodeType


def generate_end_date(node):
    return node.year + 10


def generate_node_identity(node: Node) -> NodeIdentity:
    return NodeIdentity(code=node.code, year=node.year)


class NodeFactory(factory.Factory):

    node_id = factory.Sequence(lambda n: n+1)
    code = factory.Sequence(lambda n: 'OSIS%03dR' % n)
    title = factory.Sequence(lambda n: 'ACRONYM%02d' % n)
    year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)
    start_year = factory.SelfAttribute("year")
    end_date = factory.LazyAttribute(generate_end_date)
    entity_id = factory.LazyAttribute(generate_node_identity)


class CampusFactory(factory.Factory):

    class Meta:
        model = Campus
        abstract = False

    name = factory.Sequence(lambda n: 'Campus%02d' % n)
    university_name = factory.Sequence(lambda n: 'University%02d' % n)


class NodeGroupYearFactory(NodeFactory):

    class Meta:
        model = NodeGroupYear
        abstract = False

    node_type = factory.fuzzy.FuzzyChoice(TrainingType)
    group_title_fr = factory.fuzzy.FuzzyText(length=240)
    group_title_en = factory.fuzzy.FuzzyText(length=240)
    remark_fr = factory.fuzzy.FuzzyText(length=240)
    remark_en = factory.fuzzy.FuzzyText(length=240)
    offer_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_title_en = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_fr = factory.fuzzy.FuzzyText(length=240)
    offer_partial_title_en = factory.fuzzy.FuzzyText(length=240)
    version_title_fr = None
    version_title_en = None
    end_year = factory.SelfAttribute('.end_date')
    children = factory.LazyFunction(list)
    teaching_campus = factory.SubFactory(CampusFactory)
    constraint_type = factory.fuzzy.FuzzyChoice(ConstraintTypes)
    min_constraint = 0
    max_constraint = 5
    version_name = STANDARD
    transition_name = NOT_A_TRANSITION

    class Params:
        minitraining = factory.Trait(
            node_type=factory.fuzzy.FuzzyChoice(MiniTrainingType)
        )
        group = factory.Trait(
            node_type=factory.fuzzy.FuzzyChoice(GroupType)
        )
        listchoice = factory.Trait(
            node_type=factory.fuzzy.FuzzyChoice(GroupType.minor_major_option_list_choice_enums())
        )


class NodeLearningUnitYearFactory(NodeFactory):

    class Meta:
        model = NodeLearningUnitYear
        abstract = False

    node_type = NodeType.LEARNING_UNIT
    code = factory.Sequence(lambda n: 'LUCODE%02d' % n)
    credits = factory.fuzzy.FuzzyDecimal(0, 10, precision=1)
    specific_title_en = factory.fuzzy.FuzzyText(length=240)
    common_title_en = factory.fuzzy.FuzzyText(length=240)
    learning_unit_type = factory.fuzzy.FuzzyChoice(LearningContainerYearType)
