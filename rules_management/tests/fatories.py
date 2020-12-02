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

import factory
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class PermissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Permission

    name = factory.Faker('text', max_nb_chars=255)
    codename = factory.Faker('text', max_nb_chars=100)
    content_type = factory.Iterator(ContentType.objects.all())


class FieldReferenceFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'rules_management.FieldReference'

    content_type = factory.Iterator(ContentType.objects.all())
    field_name = "acronym"

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of permissions were passed in, use them
            for permission in extracted:
                self.permissions.add(permission)
