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
from typing import List

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from ddd.logic.learning_unit.business_types import *


class AcademicYearLowerThan2019Exception(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Can't create a learning unit lower than 2019-20")
        super().__init__(message, **kwargs)


class InvalidResponsibleEntityTypeOrCodeException(BusinessException):
    def __init__(self, entity_code: str, *args, **kwargs):
        message = _(
            "Selected entity {} is not an authorized responsible entity".format(entity_code)
        )
        super().__init__(message, **kwargs)


class CreditsShouldBeGreatherThanZeroException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _(
            "Credits should be greather than 0"
        )
        super().__init__(message, **kwargs)


class LearningUnitCodeAlreadyExistsException(BusinessException):
    def __init__(self, code: str, *args, **kwargs):
        message = _(
            "The code {} already exists"
        ).format(code)
        super().__init__(message, **kwargs)


class LearningUnitCodeStructureInvalidException(BusinessException):
    def __init__(self, code: str, *args, **kwargs):
        message = _("The code {} is not a valid code").format(code)
        super().__init__(message, **kwargs)


class EmptyRequiredFieldsException(BusinessException):
    def __init__(self, empty_required_fields: List[str], *args, **kwargs):
        message = _("Following fields are required : {}").format(empty_required_fields)
        super().__init__(message, **kwargs)


class LearningUnitUsedInProgramTreeException(BusinessException):
    def __init__(
            self,
            learning_unit: 'LearningUnitIdentity',
            program_identities: List['ProgramTreeIdentity'],
            *args,
            **kwargs
    ):
        message = _("Learning unit {} is used in following programs : {}").format(
            learning_unit,
            ",".join([identity.code for identity in program_identities])
        )
        super().__init__(message, **kwargs)


class InternshipSubtypeMandatoryException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Internship subtype is a mandatory field")
        super().__init__(message, **kwargs)


class LearningUnitAlreadyExistsException(BusinessException):
    def __init__(self, learning_unit_identity: 'LearningUnitIdentity', *args, **kwargs):
        message = _("Learning unit {} already exists next year").format(learning_unit_identity)
        super().__init__(message, **kwargs)


class SubdivisionShouldHaveOneLetterException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("The subdivision must contain only one letter")
        super().__init__(message, **kwargs)


class SubdivisionAlreadyExistException(BusinessException):
    def __init__(self, learning_unit_identity: 'LearningUnitIdentity', subdivision: str, *args, **kwargs):
        message = _("The subdivision {subd} already exists for {ue}").format(
            subd=subdivision,
            ue=learning_unit_identity,
        )
        super().__init__(message, **kwargs)
