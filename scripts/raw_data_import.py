##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import csv
from django.db import IntegrityError
from base import models as mdl


# To be removed once all program managers are imported.
def load_program_managers():
    with open('program-managers.csv') as csvfile:
        row = csv.reader(csvfile)
        imported_counter = 0
        error_counter = 0
        duplication_counter = 0
        for columns in row:
            if len(columns) > 0:
                offer_years = mdl.offer_year.find_by_acronym(columns[0].strip())
                person = mdl.person.find_by_global_id(columns[2].strip())

                if offer_years:
                    if person:
                        for offer_year in offer_years:
                            program_manager = mdl.program_manager.ProgramManager()
                            program_manager.offer_year = offer_year
                            program_manager.person = person
                            try:
                                program_manager.save()
                                print('Saved : %s - %s' % (offer_year, person))
                                imported_counter += 1
                            except IntegrityError:
                                print('Duplicated : %s - %s' % (offer_year, person))
                                duplication_counter += 1
                    else:
                        error_counter += 1
                        print(u'No person named "%s" for "%s", "%s", "%s"' % (person, columns[0], columns[1], columns[2]))
                else:
                    error_counter += 1
                    print(u'No offer year named "%s" for "%s", "%s", "%s"' % (columns[0], columns[1], columns[2], person))
        print(u'%d program managers imported.' % imported_counter)
        print(u'%d program managers not imported.' % error_counter)
        print(u'%d program managers duplicated.' % duplication_counter)
