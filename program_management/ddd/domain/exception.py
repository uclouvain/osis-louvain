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
from program_management.ddd.business_types import *
from osis_common.ddd.interface import BusinessException
from django.utils.translation import gettext_lazy as _


class RelativeCreditShouldBeGreaterOrEqualsThanZero(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Relative credits must be greater or equals than 0")
        super().__init__(message, **kwargs)


class ProgramTreeNotFoundException(Exception):
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
