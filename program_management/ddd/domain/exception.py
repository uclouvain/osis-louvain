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

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException, BusinessExceptions
from program_management.ddd.business_types import *


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
            "in {year} as specific versions exists during this year."
        ).format(
            code=tree.program_tree_identity.code,
            year=tree.entity_id.year,
        )
        super().__init__(message, **kwargs)


class NodeIsUsedException(Exception):
    pass


# TODO : use BusinessException instead of BusinessExceptions
class ProgramTreeVersionMismatch(BusinessExceptions):
    def __init__(
            self,
            root_version_identity: 'ProgramTreeVersionIdentity',
            child_version_identity: 'ProgramTreeVersionIdentity',
            *args,
            **kwargs
    ):
        root_node_version_title = self._get_version_title(root_version_identity)
        node_to_add_version_title = self._get_version_title(child_version_identity)
        root_code = kwargs.pop('root_code')
        child_code = kwargs.pop('child_code')
        messages = [_("%(node_to_add)s version must be the same as %(root_node)s version") % {
            'node_to_add': '{} - {}'.format(child_code, node_to_add_version_title),
            'root_node': '{} - {}'.format(root_code, root_node_version_title)
        }]
        super().__init__(messages, **kwargs)

    def _get_version_title(self, version_identity):
        return "{}[{}]".format(
            version_identity.offer_acronym, version_identity.version_name
        ) if version_identity.version_name else version_identity.offer_acronym


class Program2MEndDateShouldBeGreaterOrEqualThanItsFinalities(BusinessException):
    def __init__(self, finality: 'Node', **kwargs):
        message = _("The end date must be higher or equal to finality %(acronym)s") % {
            "acronym": finality.title
        }
        super().__init__(message, **kwargs)
