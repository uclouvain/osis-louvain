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

from base.tests.factories.group_element_year import _generate_block_value
from base.tests.factories.utils.fuzzy import FuzzyBoolean
from program_management.ddd.domain.link import Link
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


class LinkFactory(factory.Factory):
    class Meta:
        model = Link
        abstract = False

    pk = factory.Sequence(lambda n: n+1)
    parent = factory.SubFactory(NodeGroupYearFactory)
    child = factory.SubFactory(NodeGroupYearFactory)
    relative_credits = factory.fuzzy.FuzzyInteger(0, 10)
    is_mandatory = FuzzyBoolean()
    order = None
    block = factory.LazyFunction(_generate_block_value)
    link_type = None

    @factory.post_generation
    def _add_children(self, create, extracted, ** kwargs):
        if not self.parent.children:
            self.parent.children = [self]
        else:
            self.parent.children.append(self)
