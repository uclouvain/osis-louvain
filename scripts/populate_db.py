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

import scripts.populate_base_student as populate_student
import scripts.populate_base_tutor as populate_tutor
import scripts.populate_reference_continent as populate_continent
import scripts.populate_reference_currency as populate_currency
import scripts.populate_reference_language as populate_language


populate_tutor.create_tutor_and_person_and_user()
populate_student.create_student_and_person_and_user()
populate_continent.add_continents()
populate_currency.add_currencies()
populate_language.add_languages()
