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
from django.contrib.auth import backends
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"), required=True)
    force_user_creation = serializers.BooleanField(label=_("Create user if not exists"), default=False)

    def validate(self, attrs):
        UserModel = backends.get_user_model()
        user_kwargs = {UserModel.USERNAME_FIELD: attrs['username']}

        if attrs['force_user_creation']:
            user, created = UserModel.objects.get_or_create(**user_kwargs)
        else:
            try:
                user = UserModel.objects.get(**user_kwargs)
            except UserModel.DoesNotExist:
                msg = _('Unable to find username provided.')
                raise serializers.ValidationError({'username': msg})
        attrs['user'] = user
        return attrs
