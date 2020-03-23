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
from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from osis_role import role


class Command(BaseCommand):
    help = 'Synchronize all declared osis-roles with default RBAC (Role Based Access Control - groups table) ' \
           'provided by Django'

    def handle(self, *args, **options):
        for role_mdl in role.role_manager.roles:
            group, _ = Group.objects.get_or_create(name=role_mdl.group_name)

            self._add_all_perms_to_role(role_mdl, group)
            self._remove_unused_perms_in_group(role_mdl, group)
            self.stdout.write(self.style.SUCCESS('Perms-Role {} successfully synchronized'.format(role_mdl.group_name)))

    def _add_all_perms_to_role(self, role, group):
        for perm_codename in role.rule_set().keys():
            try:
                perm = Permission.objects.get(codename=perm_codename)
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                warning_msg = 'Permission {} does not exist - defined in {}'.format(perm_codename, role.group_name)
                self.stdout.write(self.style.WARNING(warning_msg))

    def _remove_unused_perms_in_group(self, role, group):
        permissions_to_remove = group.permissions.exclude(codename__in=role.rule_set().keys())
        group.permissions.remove(*permissions_to_remove)
