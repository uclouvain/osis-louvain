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

from features.pages.learning_unit import pages


def fill_form_for_faculty(page: pages.LearningUnitEditPage) -> dict:
    form_data = {
        "actif": bool(random.randint(0, 1)),
        "session_derogation": random.choice(page.session_derogation.options).text,
        "quadrimester": random.choice(page.quadrimestre.options).text,
    }

    page.actif = form_data["actif"]
    page.session_derogation = form_data["session_derogation"]
    page.quadrimestre = form_data["quadrimester"]

    return form_data


def fill_form_for_central(page: pages.LearningUnitEditPage) -> dict:
    form_data = {
        "actif": bool(random.randint(0, 1)),
        "session_derogation": random.choice(page.session_derogation.options).text,
        "quadrimester": random.choice(page.quadrimestre.options).text,
        "credits": random.randint(1, 10),
        "perdiodicity": random.choice(page.periodicite.options).text,
    }

    page.actif = form_data["actif"]
    page.session_derogation = form_data["session_derogation"]
    page.quadrimestre = form_data["quadrimester"]
    page.credits = form_data["credits"]
    page.periodicite = form_data["perdiodicity"]

    return form_data
