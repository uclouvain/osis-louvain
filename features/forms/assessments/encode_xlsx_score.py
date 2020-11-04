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
import random

from openpyxl import load_workbook

SCORE_STARTING_ROW = 13


def update_xlsx(filename):
    wb = load_workbook(filename)

    sheet = wb.active
    scores = []

    current_row = SCORE_STARTING_ROW
    while sheet['E{}'.format(current_row)].value:
        score_or_justification = bool(random.getrandbits(1))
        selected_column = 'I' if score_or_justification else 'J'

        if score_or_justification:
            value = str(random.randint(0, 20))
        else:
            value = random.choice(('A', 'T'))

        sheet['{}{}'.format(selected_column, current_row)] = value
        scores.append(value)
        current_row += 1

    wb.save(filename=filename)
    return scores
