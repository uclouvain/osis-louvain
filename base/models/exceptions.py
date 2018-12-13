##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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


class StartDateHigherThanEndDateException(Exception):
    def __init__(self, message=None, errors=None):
        super(StartDateHigherThanEndDateException, self).__init__(message)
        self.errors = errors


class TxtLabelOrderExitsException(Exception):
    def __init__(self, message=None, errors=None):
        super(TxtLabelOrderExitsException, self).__init__(message)
        self.errors = errors


class TxtLabelOrderMustExitsException(Exception):
    def __init__(self, message=None, errors=None):
        super(TxtLabelOrderMustExitsException, self).__init__(message)
        self.errors = errors


class JustificationValueException(Exception):
    def __init__(self, message=None, errors=None):
        super(JustificationValueException, self).__init__(message)
        self.errors = errors


class MaximumOneParentAllowedException(Exception):
    def __init__(self, message=None, errors=None):
        super(MaximumOneParentAllowedException, self).__init__(message)
        self.errors = errors


class IncompatiblesTypesException(Exception):
    def __init__(self, message=None, errors=None):
        super(IncompatiblesTypesException, self).__init__(message)
        self.errors = errors


class MaxChildrenReachedException(Exception):
    def __init__(self, message=None, errors=None):
        super(MaxChildrenReachedException, self).__init__(message)
        self.errors = errors
