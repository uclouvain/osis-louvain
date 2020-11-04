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
import subprocess
import sys

from base.management.commands import makemessages


class MessagesNotTranslatedException(Exception):
    pass


class Command(makemessages.Command):
    def handle(self, *args, **options):
        options['keep_pot'] = True
        options['verbosity'] = 0

        super().handle(*args, **options)

        self.check_all_messages_are_translated()

    def check_all_messages_are_translated(self):
        fr_po_file_location = "locale/fr_BE/LC_MESSAGES/django.po"
        pot_file_location = "locale/django.pot"

        try:
            subprocess.run(
                ["msgcmp", fr_po_file_location, pot_file_location],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.stderr.write(e.stderr)
            raise SystemExit(1)
        finally:
            self.remove_potfiles()

    def write_po_file(self, potfile, locale):
        #  don't need to overwrite existing po file
        pass
