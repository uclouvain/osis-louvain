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
from django.utils.translation import gettext as _

from base.ddd.utils.business_validator import BusinessListValidator
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeEducationGroupYear, NodeGroupYear, NodeLearningUnitYear
from program_management.ddd.validators._authorized_relationship import \
    AuthorizedRelationshipLearningUnitValidator, AttachAuthorizedRelationshipValidator
from program_management.ddd.validators._detach_root import DetachRootForbiddenValidator
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityValidator
from program_management.ddd.validators._minimum_editable_year import \
    MinimumEditableYearValidator
from program_management.ddd.validators._node_duplication import NodeDuplicationValidator
from program_management.ddd.validators._parent_as_leaf import ParentIsNotLeafValidator
from program_management.ddd.validators._parent_child_academic_year import ParentChildSameAcademicYearValidator


class AttachNodeValidatorList(BusinessListValidator):

    success_messages = [
        _('Success message')
    ]

    def __init__(self, tree: 'ProgramTree', node_to_add: 'Node', path: 'Path'):

        # TODO :: instancier les validators directement, plutôt que d'avoir des classes (les paramètres changent)
        if isinstance(node_to_add, NodeEducationGroupYear) or isinstance(node_to_add, NodeGroupYear):

            self.validators = [
                ParentIsNotLeafValidator,
                AttachAuthorizedRelationshipValidator,
                NodeDuplicationValidator,
                MinimumEditableYearValidator,
                InfiniteRecursivityValidator,
                ParentChildSameAcademicYearValidator,
            ]

        elif isinstance(node_to_add, NodeLearningUnitYear):

            self.validators = [
                ParentIsNotLeafValidator,
                AuthorizedRelationshipLearningUnitValidator,
                NodeDuplicationValidator,
                MinimumEditableYearValidator,
                InfiniteRecursivityValidator,
                DetachRootForbiddenValidator,
                ParentChildSameAcademicYearValidator,
            ]

        else:
            raise AttributeError("Unknown instance of node")

        super(AttachNodeValidatorList, self).__init__(validator_args=[tree, node_to_add, tree.get_node(path)])
