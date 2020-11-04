# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

SUCCESS_EXIT_CODE = 0


class TestMigrations(TestCase):
    def test_should_not_create_new_migrations_files_when_makemigrations_is_called(self):
        out = StringIO()
        try:
            call_command("makemigrations", dry_run=True, check=True, stdout=out)
        except SystemExit as e:
            error_msg = "Some models changes has no migrations file.\n" \
                        "Migrations file that would be created:\n" \
                        "{}".format(out.getvalue())
            self.assertEqual(e.code, SUCCESS_EXIT_CODE, error_msg)
