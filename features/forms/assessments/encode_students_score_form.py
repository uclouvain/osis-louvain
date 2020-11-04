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
import random

from features.pages.assessments import pages


def fill_one_student_score(
        page: pages.ScoreEncodingFormPage,
) -> list:
    number_students = len(page.results)
    scores_to_encode = [""] * number_students

    index_of_student_to_encode_score = random.randint(0, number_students)
    random_score = _get_random_score()

    page.results[index_of_student_to_encode_score].score = random_score
    scores_to_encode[index_of_student_to_encode_score] = random_score

    return scores_to_encode


def fill_student_scores(
        page: pages.ScoreEncodingFormPage,
) -> list:
    number_students = len(page.results)
    scores_to_encode = [_get_random_score() for _ in range(number_students)]

    for student, score in zip(page.results, scores_to_encode):
        student.score = score

    return scores_to_encode


def clear_all_scores(
        page: pages.ScoreEncodingFormPage
) -> list:
    number_students = len(page.results)
    scores_to_encode = [""] * number_students

    for student, score in zip(page.results, scores_to_encode):
        student.score = score

    return scores_to_encode


def _get_random_score() -> str:
    return str(random.randint(0, 20))

