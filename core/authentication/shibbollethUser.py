##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
# designed to manage the core business of higher education institutions,
# such as universities, faculties, institutes and professional schools.
# The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib import auth
from django.contrib.auth import backends
from django.core.exceptions import ImproperlyConfigured
from core.models import Person


class ShibbollethUserBackend(RemoteUserBackend):
    def authenticate(self, remote_user, user_infos):
        """
        The username passed as ``remote_user`` is considered trusted.  This
        method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """
        if not remote_user:
            return
        user = None
        username = self.clean_username(remote_user)

        UserModel = backends.get_user_model()

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = UserModel._default_manager.get_or_create(**{
                UserModel.USERNAME_FIELD: username
            })
            if created:
                user = self.configure_user(user, user_infos)
        else:
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass
        user = self.__update_user(user, user_infos)
        self.__update_person(user, user_infos)
        return user

    def clean_username(self, username):
        return username.split("@")[0]

    def configure_user(self, user, user_infos):
        user.last_name = user_infos['USER_LAST_NAME']
        user.first_name = user_infos['USER_FIRST_NAME']
        user.email = user_infos['USER_EMAIL']
        user.save()
        return user

    def __update_user(self, user, user_infos):
        user.first_name = user_infos['USER_FIRST_NAME']
        user.last_name = user_infos['USER_LAST_NAME']
        user.save()
        return user

    def __update_person(self, user, user_infos):
        persons = Person.objects.filter(user=user)
        if not persons:
            person = Person(user=user, global_id=user_infos['USER_FGS'], first_name=user_infos['USER_FIRST_NAME'],
                            last_name=user_infos['USER_LAST_NAME'])
        else:
            person = persons[0]
            person.first_name = user.first_name
            person.last_name = user.last_name
        person.save()


class ShibbollethUserMiddleware(RemoteUserMiddleware):
    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")
        try:
            username = request.META[self.header]
        except KeyError:
            # If specified header doesn't exist then remove any existing
            # authenticated remote-user, or return (leaving request.user set to
            # AnonymousUser by the AuthenticationMiddleware).
            if request.user.is_authenticated():
                self._remove_invalid_user(request)
            return
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated():
            if request.user.get_username() == self.clean_username(username, request):
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user_infos = self.get_shibbolleth_infos(request)
        user = auth.authenticate(remote_user=username, user_infos=user_infos)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

    def get_shibbolleth_infos(self, request):
        user_first_name = request.META['givenName']
        user_last_name = request.META['sn']
        user_email = request.META['mail']
        employee_number_len = len(request.META['employeeNumber'])
        prefix_fgs = (8 - employee_number_len) * '0'
        user_fgs = ''.join([prefix_fgs, request.META['employeeNumber']])
        user_infos = {'USER_FIRST_NAME': user_first_name, 'USER_LAST_NAME': user_last_name, 'USER_EMAIL': user_email,
                      'USER_FGS': user_fgs}
        return user_infos
