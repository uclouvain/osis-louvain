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
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from base.models.person import Person


class PermissionDecorator:
    """
    This class creates generic decorators to check if the user is allowed to access the data

    Decorators need 3 attributes :
        - permission_method : method to call to validate the permission
        - argument_name : the argument name to get the object to validate
        - argument_instance : the object type to validate
        - permission_denied_msg : if we want to add a message if permission denied

    """
    def __init__(self, permission_method, argument_name, argument_instance, permission_denied_msg=None):
        self.permission_method = permission_method
        self.permission_denied_message = permission_denied_msg or "The user can not access this page"
        self.argument_instance = argument_instance
        self.argument_name = argument_name

    def __call__(self, view_func):
        @login_required
        def wrapped_f(*args, **kwargs):
            # Retrieve objects
            obj = get_object_or_404(self.argument_instance, pk=kwargs.get(self.argument_name))

            # Check permission
            if not self._call_permission_method(args[0], obj):
                raise PermissionDenied(self.permission_denied_message)

            # Call the view
            return view_func(*args, **kwargs)

        return wrapped_f

    def _call_permission_method(self, request, obj):
        person = get_object_or_404(Person, user=request.user)
        return self.permission_method(obj, person)
