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
from django.dispatch import receiver

from assessments.business import scores_encodings_deadline
from base.signals import publisher


@receiver(publisher.compute_scores_encodings_deadlines)
def compute_scores_encodings_deadlines(sender, **kwargs):
    scores_encodings_deadline.compute_deadline(kwargs['offer_year_calendar'])


@receiver(publisher.compute_student_score_encoding_deadline)
def compute_student_score_encoding_deadline(sender, **kwargs):
    scores_encodings_deadline.compute_deadline_by_student(kwargs['session_exam_deadline'])


@receiver(publisher.compute_all_scores_encodings_deadlines)
def compute_all_scores_encodings_deadlines(sender, **kwargs):
    scores_encodings_deadline.recompute_all_deadlines(kwargs['academic_calendar'])
