# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import sys
from importlib import import_module

from behave.__main__ import main as behave_main
from behave_django.environment import monkey_patch_behave
from behave_django.management.commands.behave import Command as Cmd

from features.runner import OsisRunner


class Command(Cmd):
    def handle(self, *args, **options):
        # Check the flags
        if options['use_existing_database'] and options['simple']:
            self.stderr.write(self.style.WARNING(
                '--simple flag has no effect'
                ' together with --use-existing-database'
            ))

        # Configure django environment
        passthru_args = ('failfast',
                         'interactive',
                         'keepdb',
                         'reverse')
        runner_args = {k: v for
                       k, v in
                       options.items() if k in passthru_args and v is not None}
        django_test_runner = OsisRunner(**runner_args)
        django_test_runner.setup_test_environment()
        old_config = django_test_runner.setup_databases()

        # Run Behave tests
        monkey_patch_behave(django_test_runner)
        behave_args = self.get_behave_args()
        exit_status = behave_main(args=behave_args)

        # Teardown django environment
        OsisRunner.testcase_class()._flush_db()
        django_test_runner.teardown_databases(old_config)
        django_test_runner.teardown_test_environment()

        if exit_status != 0:
            sys.exit(exit_status)


def import_class(path):
    mod, cls = path.rsplit(".", 1)
    return getattr(import_module(mod), cls)
