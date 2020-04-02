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
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import BaseCommand
from django.db.models import Q

from osis_role import role


class Command(BaseCommand):
    help = 'Synchronize all declared osis-roles (=groups) with user in table which are defined in OsisRoleManager'

    def handle(self, *args, **options):
        for role_mdl in role.role_manager.roles:
            group, _ = Group.objects.get_or_create(name=role_mdl.group_name)

            users_to_add = self._get_users_in_role_model_but_not_in_auth_groups(role_mdl)
            group.user_set.add(*users_to_add)

            users_to_delink = self._get_users_in_auth_groups_but_not_in_role_model(role_mdl)
            group.user_set.remove(*users_to_delink)

            self.stdout.write(self.style.SUCCESS('Role {} successfully synchronized'.format(role_mdl.group_name)))

    def _get_users_in_role_model_but_not_in_auth_groups(self, role_mdl):
        subqs = role_mdl.objects.exclude(
            person__user__groups__name=role_mdl.group_name
        ).value_list('person__user_id', flat=True)
        return get_user_model().objects.filter(pk__in=subqs)

    def _get_users_in_auth_groups_but_not_in_role_model(self, role_mdl):
        return get_user_model().objects.filter(
            Q(groups__name=role_mdl.group_name) &
            ~Q(pk__in=role_mdl.objects.value_list('person__user_id', flat=True))
        )
