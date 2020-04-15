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

from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory


class RoleModelFactory(factory.DjangoModelFactory):
    class Meta:
        abstract = True

    person = factory.SubFactory(PersonFactory)

    @factory.post_generation
    def add_relevant_permissions_to_user_group(self, create, extracted, **kwargs):
        permissions = []
        for perm_name in self.rule_set().keys():
            app_label, codename = perm_name.split('.')
            try:
                perm_obj = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                permissions.append(perm_obj)
            except Permission.DoesNotExist:
                pass
        self.person.user.groups.get(name=self.group_name).permissions.set(permissions)


class EntityModelFactory(RoleModelFactory):
    class Meta:
        abstract = True
        django_get_or_create = ('person', 'entity',)

    entity = factory.SubFactory(EntityFactory)
    with_child = False
