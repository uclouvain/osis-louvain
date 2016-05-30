##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import connection
from django.db import transaction


@transaction.atomic
def execute(sql_command):
    results = []
    if sql_command:
        with connection.cursor() as cursor:
            sql_commands = sql_command.split(";")
            for count, command in enumerate(sql_commands):
                if command.strip():
                    try:
                        cursor.execute(command.strip())
                        results += [u'%d: %s\n> %s\n\n' % (count + 1, command.strip(), cursor.fetchall())]
                    except Exception as e:
                        results += [u'%d: %s\n> %s\n\n' % (count + 1, command.strip(), e)]
    return results
