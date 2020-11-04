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

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-g', '--group', type=str, help='Define group to synchronize', )

    def handle(self, *args, **options):
        roles_to_sync = role.role_manager.roles if not options.get('group') else \
            filter(lambda r: r.group_name == options.get('group'), role.role_manager.roles)

        for role_mdl in roles_to_sync:
            group, _ = Group.objects.get_or_create(name=role_mdl.group_name)

            self._add_all_perms_to_role(role_mdl, group)
            self._remove_unused_perms_in_group(role_mdl, group)
            self.stdout.write(self.style.SUCCESS('Perms-Role {} successfully synchronized'.format(role_mdl.group_name)))

    def _add_all_perms_to_role(self, role, group):
        perm_list = self._get_perm_obj_list(role)
        group.permissions.add(*perm_list)

    def _remove_unused_perms_in_group(self, role, group):
        perm_list_ids = [perm.pk for perm in self._get_perm_obj_list(role)]
        permissions_to_remove = group.permissions.exclude(pk__in=perm_list_ids)
        group.permissions.remove(*permissions_to_remove)

    def _get_perm_obj_list(self, role):
        perm_list = []
        for perm_name in role.rule_set().keys():
            try:
                app_label, codename = perm_name.split('.')
                perm_list.append(
                    Permission.objects.get(content_type__app_label=app_label, codename=codename)
                )
            except Permission.DoesNotExist:
                warning_msg = 'Permission {} does not exist - defined in {}'.format(perm_name, role.group_name)
                self.stdout.write(self.style.WARNING(warning_msg))
        return perm_list
