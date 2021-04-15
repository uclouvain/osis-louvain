##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
from abc import abstractmethod
from typing import List

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import EntityIdentity, CommandRequest, ApplicationServiceResult


class DisplayExceptionsByFieldNameMixin:
    """
    This Mixin provides a fonction 'display_exceptions'
    used to display business validation messages (business Exceptions)
    inside defined fields in the attribute 'field_name_by_exception'
    """

    # Dict[Exception, Tuple[FormFieldNameStr]]
    # Example : {CodeAlreadyExistException: ('code',), AcronymAlreadyExist: ('acronym',)}
    field_name_by_exception = None

    # If True, exceptions that are not configured in `field_name_by_exception` will be displayed.
    # If False, exceptions that are not configured in `field_name_by_exception` will be ignored.
    display_exceptions_by_default = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.field_name_by_exception is None:
            self.field_name_by_exception = {}

    @abstractmethod
    def get_command(self) -> CommandRequest:
        raise NotImplementedError
        # return self.get_colmmand_class(**self.validated_data)  # FIXME ::

def save(self):
        try:
            if self.is_valid():
                return message_bus_instance.invoke(self.get_command())
        except MultipleBusinessExceptions as multiple_exceptions:
            self.display_exceptions(multiple_exceptions)

    def display_exceptions(self, exceptions_to_display: MultipleBusinessExceptions):
        """
        Add the exception messages in the fields specified in the 'field_name_by_exception' attribute.
        Add a generic error by default if no fields are defined.
        :param exceptions_to_display: MultipleBusinessExceptions
        :return:
        """
        self.__check_if_fields_exists()
        copied_list = list(exceptions_to_display.exceptions)
        for exception in copied_list:
            field_names = self.field_name_by_exception.get(type(exception), [])
            if self.display_exceptions_by_default and not field_names:
                self.add_error('', exception.message)
            else:
                for field_name in field_names:
                    self.add_error(field_name, exception.message)
            exceptions_to_display.exceptions.remove(exception)

    def __check_if_fields_exists(self):
        all_field_names = set(itertools.chain.from_iterable(self.field_name_by_exception.values()))
        declared_field_names = set(self.declared_fields.keys())
        diff = all_field_names - declared_field_names
        if diff:
            raise ValueError("Following fields does not exist in your form : {}".format(diff))
