##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Iterable, Dict, List, Set

from django.conf import settings
from django.utils.translation import gettext_lazy as _, ngettext

from osis_common.ddd.interface import BusinessException
from program_management.ddd.business_types import *

BLOCK_MAX_AUTHORIZED_VALUE = 6


class RelativeCreditShouldBeGreaterOrEqualsThanZero(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Relative credits must be greater or equals than 0")
        super().__init__(message, **kwargs)


class RelativeCreditShouldBeLowerOrEqualThan999(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Relative credits must be lower or equals to 999")
        super().__init__(message, **kwargs)


class ProgramTreeNotFoundException(Exception):
    def __init__(self, *args, code: str = '', year: int = None):
        message = ''
        if code or year:
            message = _("Program tree not found : {code} {year}".format(code=code, year=year))
        super().__init__(message, *args)


class NodeNotFoundException(Exception):
    pass


class ProgramTreeVersionNotFoundException(Exception):
    pass


class ProgramTreeAlreadyExistsException(Exception):
    pass


class ProgramTreeNonEmpty(BusinessException):
    def __init__(self, program_tree: 'ProgramTree', **kwargs):
        message = _("[%(academic_year)s] The content of the program is not empty.") % {
                    'academic_year': program_tree.root_node.academic_year,
                }
        super().__init__(message, **kwargs)


class NodeHaveLinkException(BusinessException):
    def __init__(self, node: 'Node', **kwargs):
        message = _("[%(academic_year)s] %(code)s has links to another training / mini-training / group") % {
                    'academic_year': node.academic_year,
                    'code': node.code
                }
        super().__init__(message, **kwargs)


class CannotCopyTreeVersionDueToEndDate(BusinessException):
    def __init__(self, tree_version: 'ProgramTreeVersion', *args, **kwargs):
        message = _(
            "You can't copy the program tree version '{acronym}' "
            "from {from_year} to {to_year} because it ends in {end_year}"
        ).format(
            acronym=tree_version.entity_id.offer_acronym,
            from_year=tree_version.get_tree().root_node.year,
            to_year=tree_version.get_tree().root_node.year + 1,
            end_year=tree_version.get_tree().root_node.end_year,
        )
        super().__init__(message, **kwargs)


class CannotCopyTreeDueToEndDate(BusinessException):
    def __init__(self, tree: 'ProgramTree', *args, **kwargs):
        message = _(
            "You can't copy the program tree '{code}' "
            "from {from_year} to {to_year} because it ends in {end_year}"
        ).format(
            code=tree.entity_id.code,
            from_year=tree.root_node.year,
            to_year=tree.root_node.year + 1,
            end_year=tree.root_node.end_year,
        )
        super().__init__(message, **kwargs)


class CannotDeleteStandardDueToVersionEndDate(BusinessException):
    def __init__(self, tree: 'ProgramTreeVersion', *args, **kwargs):
        message = _(
            "You can't delete the standard program tree '{code}' "
            "in {year} as specific versions exists during this year and/or in the future."
        ).format(
            code=tree.program_tree_identity.code,
            year=tree.entity_id.year,
        )
        super().__init__(message, **kwargs)


class NodeIsUsedException(Exception):
    pass


class ProgramTreeVersionMismatch(BusinessException):
    def __init__(
            self,
            node_to_add: 'Node',
            node_to_paste_to: 'Node',
            parents_version_mismatched_identity: List['ProgramTreeVersionIdentity'],
            *args,
            **kwargs
    ):
        parents_version_names = {
            self._get_version_name(version_identity) for version_identity in parents_version_mismatched_identity
        }
        messages = _(
            "%(node_to_add)s or its children must have the same version as %(node_to_paste_to)s "
            "and all of it's parent's [%(version_mismatched)s]"
        ) % {
            'node_to_add': str(node_to_add),
            'node_to_paste_to': str(node_to_paste_to),
            'version_mismatched': ",".join(parents_version_names)
        }
        super().__init__(messages, **kwargs)

    def _get_version_name(self, version_identity: 'ProgramTreeVersionIdentity'):
        return str(_('Standard')) if version_identity.is_official_standard else version_identity.version_name


class Program2MEndDateLowerThanItsFinalitiesException(BusinessException):
    def __init__(self, node_2m: 'Node', **kwargs):
        message = _("The end date of %(acronym)s must be higher or equal to its finalities") % {
            "acronym": node_2m.title
        }
        super().__init__(message, **kwargs)


class FinalitiesEndDateGreaterThanTheirMasters2MException(BusinessException):
    def __init__(self, root_node: 'Node', finalities: List['Node']):
        message = ngettext(
            "Finality \"%(acronym)s\" has an end date greater than %(root_acronym)s program.",
            "Finalities \"%(acronym)s\" have an end date greater than %(root_acronym)s program.",
            len(finalities)
        ) % {
            "acronym": ', '.join([node.title for node in finalities]),
            "root_acronym": root_node.title
        }
        super().__init__(message)


class CannotAttachOptionIfNotPresentIn2MOptionListException(BusinessException):
    def __init__(self, root_node: 'Node', options: List['Node']):
        message = ngettext(
            "Option \"%(code)s\" must be present in %(root_code)s program.",
            "Options \"%(code)s\" must be present in %(root_code)s program.",
            len(options)
        ) % {
            "code": ', '.join([str(option) for option in options]),
            "root_code": root_node
        }
        super().__init__(message)


class ReferenceLinkNotAllowedWithLearningUnitException(BusinessException):
    def __init__(self, learning_unit_node: 'Node', **kwargs):
        message = _("You are not allowed to create a reference with a learning unit %(child_node)s") % {
            "child_node": learning_unit_node
        }
        super().__init__(message, **kwargs)


class LinkShouldBeReferenceException(BusinessException):
    def __init__(self, parent_node: 'Node', child_node: 'Node', **kwargs):
        message = _("Link type should be reference between %(parent)s and %(child)s") % {
            "parent": parent_node,
            "child": child_node
        }
        super().__init__(message, **kwargs)


class ReferenceLinkNotAllowedException(BusinessException):
    def __init__(self, parent_node: 'Node', child_node: 'Node', reference_childrens: Iterable['Node'], **kwargs):
        message = _(
            "Link between %(parent)s and %(child)s cannot be of reference type "
            "because of its children: %(children)s"
        ) % {
            "parent": self._format_node(parent_node),
            "child": self._format_node(child_node),
            "children": ", ".join([self._format_node(reference_children) for reference_children in reference_childrens])
        }
        super().__init__(message, **kwargs)

    def _format_node(self, node: 'Node') -> str:
        return "{} ({})".format(str(node), node.node_type.value)


class InvalidBlockException(BusinessException):
    def __init__(self):
        message = _(
            "Please register a maximum of %(max_authorized_value)s digits in ascending order, "
            "without any duplication. Authorized values are from 1 to 6. Examples: 12, 23, 46"
        ) % {'max_authorized_value': BLOCK_MAX_AUTHORIZED_VALUE}
        super().__init__(message)


class BulkUpdateLinkException(Exception):
    def __init__(self, exceptions: Dict[str, 'MultipleBusinessExceptions']):
        self.exceptions = exceptions


class CannotPasteToLearningUnitException(BusinessException):
    def __init__(self, parent_node):
        message = _("Cannot add any element to learning unit %(parent_node)s") % {
            "parent_node": parent_node
        }
        super().__init__(message)


class CannotAttachSameChildToParentException(BusinessException):
    def __init__(self, child_node):
        message = _("You can not add the same child %(child_node)s several times.") % {"child_node": child_node}
        super().__init__(message)


class CannotAttachParentNodeException(BusinessException):
    def __init__(self, child_node: 'Node'):
        message = _('The child %(child)s you want to attach is a parent of the node you want to attach.') % {
            'child': child_node
        }
        super().__init__(message)


class ParentAndChildMustHaveSameAcademicYearException(BusinessException):
    def __init__(self, parent_node, child_node):
        message = _(
            "It is prohibited to attach a %(child_node)s to an element of "
            "another academic year %(parent_node)s."
        ) % {
            "child_node": child_node,
            "parent_node": parent_node
        }
        super().__init__(message)


class CannotPasteNodeToHimselfException(BusinessException):
    def __init__(self, child_node: 'Node'):
        message = _('Cannot attach a node %(node)s to himself.') % {"node": child_node}
        super().__init__(message)


class ChildTypeNotAuthorizedException(BusinessException):
    def __init__(self, parent_node: 'Node', children_nodes: List['Node']):
        message = _(
            "You cannot add \"%(child)s\" to \"%(parent)s\" of type \"%(parent_type)s\""
        ) % {
            'child': ', '.join([self._format_node(children_node) for children_node in children_nodes]),
            'parent': parent_node,
            'parent_type': parent_node.node_type.value,
        }
        super().__init__(message)

    def _format_node(self, node: 'Node') -> str:
        return "{} ({})".format(str(node), node.node_type.value)


class MaximumChildTypesReachedException(BusinessException):
    def __init__(self, parent_node: 'Node', node_types):
        message = _(
            "The parent \"%(parent)s\" has reached the maximum number of children "
            "allowed for the type(s) : \"%(child_types)s\".") % {
            'child_types': ','.join([str(node_type.value) for node_type in node_types]),
            'parent': parent_node
        }
        super().__init__(message)


class MinimumChildTypesNotRespectedException(BusinessException):
    def __init__(self, parent_node: 'Node', minimum_children_types_reached):
        message = _("The parent %(parent)s must have at least one child of type(s) \"%(types)s\".") % {
            "types": ','.join(str(node_type.value) for node_type in minimum_children_types_reached),
            "parent": parent_node
        }
        super().__init__(message)


class MinimumEditableYearException(BusinessException):
    def __init__(self):
        message = _("Cannot perform action on a education group before %(limit_year)s") % {
            "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION
        }
        super().__init__(message)


class CannotDetachRootException(BusinessException):
    def __init__(self):
        message = _("Cannot perform detach action on root.")
        super().__init__(message)


class CannotDetachLearningUnitsWhoArePrerequisiteException(BusinessException):
    def __init__(self, root_node: 'NodeGroupYear', nodes: Iterable['NodeLearningUnitYear']):
        message = _(
            "Cannot detach because the following learning units are prerequisite "
            "in %(formation)s: %(learning_units)s"
        ) % {
            "learning_units": ", ".join([n.code for n in nodes]),
            "formation": root_node.full_acronym(),
        }
        super().__init__(message)


class CannotDetachLearningUnitsWhoHavePrerequisiteException(BusinessException):
    def __init__(self, root_node: 'NodeGroupYear', nodes: Iterable['NodeLearningUnitYear']):
        message = _(
            "Cannot detach because the following learning units have prerequisite "
            "in %(formation)s: %(learning_units)s"
        ) % {
            "formation": root_node.full_acronym(),
            "learning_units": ", ".join([n.code for n in nodes])
        }
        super().__init__(message)


class CannotDetachOptionsException(BusinessException):
    def __init__(self, finality: 'Node', options_to_detach: Set['Node']):
        message = ngettext(
            "Option \"%(acronym)s\" cannot be detach because it is contained in %(finality_acronym)s program.",
            "Options \"%(acronym)s\" cannot be detach because they are contained in %(finality_acronym)s program.",
            len(options_to_detach)
        ) % {
            "acronym": ', '.join(str(n) for n in options_to_detach),
            "finality_acronym": finality
        }
        super().__init__(message)


class InvalidVersionNameException(BusinessException):
    def __init__(self):
        message = _("Invalid name version")
        super().__init__(message)


class InvalidTransitionNameException(BusinessException):
    def __init__(self):
        message = _("This value is invalid.")
        super().__init__(message)


class VersionNameAlreadyExist(BusinessException):
    def __init__(self, version_name: str, *args, **kwargs):
        message = _("Version name {} already exists").format(version_name)
        super().__init__(message, **kwargs)


class VersionNameExistedException(BusinessException):
    def __init__(self, version_name: str, *args, **kwargs):
        message = _("Version name {} existed").format(version_name)
        super().__init__(message, **kwargs)
