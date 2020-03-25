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

from base.models.enums.link_type import LinkTypes
from program_management.ddd.business_types import *
from program_management.models.enums.node_type import NodeType


class Link:

    def __init__(self, parent: 'Node', child: 'Node', **kwargs):
        self.parent = parent
        self.child = child
        self.relative_credits = kwargs.get('relative_credits')
        self.min_credits = kwargs.get('min_credits')
        self.max_credits = kwargs.get('max_credits')
        self.is_mandatory = kwargs.get('is_mandatory') or False
        self.block = kwargs.get('block')
        self.access_condition = kwargs.get('access_condition') or False
        self.comment = kwargs.get('comment')
        self.comment_english = kwargs.get('comment_english')
        self.own_comment = kwargs.get('own_comment')
        self.quadrimester_derogation = kwargs.get('quadrimester_derogation')
        self.link_type = kwargs.get('link_type')

    def __str__(self):
        return "%(parent)s - %(child)s" % {'parent': self.parent, 'child': self.child}

    def is_reference(self):
        return self.link_type == LinkTypes.REFERENCE


class LinkWithChildLeaf(Link):
    def __init__(self, *args, **kwargs):
        super(LinkWithChildLeaf, self).__init__(*args, **kwargs)


class LinkWithChildBranch(Link):
    pass


class LinkFactory:

    def get_link(self, parent: 'Node', child: 'Node', **kwargs) -> Link:
        if parent and parent.node_type == NodeType.LEARNING_UNIT.name:
            return LinkWithChildLeaf(parent, child, **kwargs)
        else:
            return LinkWithChildBranch(parent, child, **kwargs)


factory = LinkFactory()
