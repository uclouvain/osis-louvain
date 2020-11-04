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
import json
import os

from django.core.management import BaseCommand

from backoffice.settings.base import BASE_DIR

GROUPS_FILE_PATH = 'base/fixtures/groups.json'


class Command(BaseCommand):
    help = 'Generate a default rules-set based on groups fixtures'

    def add_arguments(self, parser):
        parser.add_argument('-g', '--group', type=str, help='Group name to generate rules_set from', )

    def handle(self, *args, **options):
        if not options['group']:
            print("Please provide group - e.g. 'manage.py get_rules_set_for_group --group program_managers'")
        else:
            with open(os.path.join(BASE_DIR, GROUPS_FILE_PATH)) as groups_file:
                groups = json.load(groups_file)
                perms = self._get_group_related_permissions(groups, options)

                if perms:
                    rules_set = self._build_rules_set(perms)
                    self._print_rules_set(rules_set)
                else:
                    print('Permissions for group {} not found'.format(options['group']))

    def _print_rules_set(self, rules_set):
        print("{")
        for rule in sorted(rules_set.items()):
            print("\t'{}': {},".format(rule[0], rule[1]))
        print("}")

    def _build_rules_set(self, perms):
        rules_set = {}
        for perm in perms:
            perm_name = perm[0]
            app_name = perm[1]
            rules_set["{}.{}".format(app_name, perm_name)] = "rules.always_allow"
        return rules_set

    def _get_group_related_permissions(self, groups, options):
        perms = []
        for group in groups:
            if group['fields']['name'] == options['group']:
                perms = group['fields']['permissions']
        return perms
