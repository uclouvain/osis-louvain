##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from attribution.models import attribution
from base.models import exam_enrollment, tutor, education_group_year
from base.models.education_group_year import EducationGroupYear
from base.models.session_exam_deadline import compute_deadline_tutor


def get_scores_encoding_progress(
        user,
        education_group_year_id,
        number_session,
        academic_year,
        learning_unit_year_ids=None
):
    queryset = exam_enrollment.get_progress_by_learning_unit_years_and_offer_years(
        user=user,
        education_group_year_id=education_group_year_id,
        session_exam_number=number_session,
        academic_year=academic_year,
        learning_unit_year_ids=learning_unit_year_ids,
        only_enrolled=True
    )

    return _sort_by_acronym([ScoreEncodingProgress(obj) for obj in queryset])


def find_related_education_group_years(score_encoding_progress_list):
    educ_group_year_ids = [
        score_encoding_progress.education_group_year_id for score_encoding_progress in score_encoding_progress_list
    ]
    return EducationGroupYear.objects.filter(pk__in=educ_group_year_ids).order_by('acronym')


def find_related_tutors(user, academic_year, session_exam_number):
    # Find all offer managed by current user
    education_group_year_ids = list(education_group_year.find_by_user(user).values_list('id', flat=True))

    learning_unit_year_ids = list(
        exam_enrollment.find_for_score_encodings(
            session_exam_number=session_exam_number,
            academic_year=academic_year,
            education_group_years=education_group_year_ids,
            with_session_exam_deadline=False
        ).distinct(
            'learning_unit_enrollment__learning_unit_year'
        ).values_list(
            'learning_unit_enrollment__learning_unit_year_id',
            flat=True
        )
    )

    tutors = tutor.find_by_learning_unit(learning_unit_year_ids)
    return sorted(tutors, key=_order_by_last_name_and_first_name)


def _order_by_last_name_and_first_name(tutor):
    # Somebody person must be first on list
    SOMEBODY_GID = '99999998'
    if tutor.person.global_id == SOMEBODY_GID:
        return ('_', '_')
    last_name = tutor.person.last_name.lower() if tutor.person.last_name else ""
    first_name = tutor.person.first_name.lower() if tutor.person.first_name else ""
    return (last_name, first_name)


def group_by_learning_unit_year(score_encoding_progress_list):
    scores_encoding_progress_grouped = []
    if score_encoding_progress_list:
        scores_encoding_progress_grouped = _group_by_learning_unit(score_encoding_progress_list)
    return _sort_by_acronym(scores_encoding_progress_grouped)


def append_related_tutors_and_score_responsibles(score_encoding_progress_list):
    tutors_grouped = _get_tutors_grouped_by_learning_unit(score_encoding_progress_list)

    for score_encoding_progress in score_encoding_progress_list:
        tutors_related = tutors_grouped.get(score_encoding_progress.learning_unit_year_id)
        score_encoding_progress.tutors = tutors_related
        score_encoding_progress.score_responsibles = [tutor for tutor in tutors_related if tutor.is_score_responsible]\
                                                      if tutors_related else None

    return score_encoding_progress_list


def filter_only_incomplete(score_encoding_progress_list):
    return [score_encoding_progress for score_encoding_progress in score_encoding_progress_list
            if score_encoding_progress.exam_enrollments_encoded != score_encoding_progress.total_exam_enrollments]


def filter_only_without_attribution(score_encoding_progress_list):
    return [score_encoding_progress for score_encoding_progress in score_encoding_progress_list
            if not score_encoding_progress.tutors]


def _get_tutors_grouped_by_learning_unit(score_encoding_progress_list):
    all_attributions = list(_find_related_attribution(score_encoding_progress_list))
    tutors_grouped_by_learning_unit = {}
    for att in all_attributions:
        tutor = att.tutor
        tutor.is_score_responsible = att.score_responsible
        tutors_grouped_by_learning_unit.setdefault(att.learning_unit_year.id, []).append(tutor)

    return tutors_grouped_by_learning_unit


def _find_related_attribution(score_encoding_progress_list):
    learning_units = [score_encoding_progress.learning_unit_year_id for score_encoding_progress in
                      score_encoding_progress_list]

    return attribution.search(list_learning_unit_year=learning_units)\
                      .order_by('tutor__person__last_name', 'tutor__person__first_name')


def _group_by_learning_unit(score_encoding_progress_list):
    group_by_learning_unit = {}
    for score_encoding_progress in score_encoding_progress_list:
        key = score_encoding_progress.learning_unit_year_id
        if key in group_by_learning_unit:
            score_encoding_progress_to_update = group_by_learning_unit[key]
            score_encoding_progress_to_update.increment_progress(score_encoding_progress)
            score_encoding_progress_to_update.increment_remaining_scores_by_deadline(score_encoding_progress)
        else:
            group_by_learning_unit[key] = score_encoding_progress
    return list(group_by_learning_unit.values())


def _sort_by_acronym(score_encoding_progress_list):
    return sorted(score_encoding_progress_list, key=lambda k: k.learning_unit_year_acronym)


class ScoreEncodingProgress:
    def __init__(self, exam_enrol: exam_enrollment.ExamEnrollment):
        self.learning_unit_year_id = exam_enrol.learning_unit_year_id
        self.learning_unit_year_acronym = exam_enrol.learning_unit_year_acronym
        self.learning_unit_year_title = ' - '.join(
            filter(None,
                   [exam_enrol.learning_container_year_common_title,
                    exam_enrol.learning_unit_year_specific_title]
                   )
        )

        self.education_group_year_id = exam_enrol.education_group_year_id
        self.exam_enrollments_encoded = exam_enrol.exam_enrollments_encoded
        self.draft_scores = exam_enrol.draft_scores
        self.scores_not_yet_submitted = exam_enrol.scores_not_yet_submitted
        self.total_exam_enrollments = exam_enrol.total_exam_enrollments
        self.remaining_scores_by_deadline = {
            compute_deadline_tutor(exam_enrol.deadline, exam_enrol.deadline_tutor): self.scores_not_yet_submitted
        }

    @property
    def progress_int(self):
        return (self.exam_enrollments_encoded / self.total_exam_enrollments) * 100

    @property
    def progress(self):
        return "{0:.0f}".format(self.progress_int)

    def increment_progress(self, score_encoding_progress):
        self.draft_scores += score_encoding_progress.draft_scores
        self.scores_not_yet_submitted += score_encoding_progress.scores_not_yet_submitted
        self.exam_enrollments_encoded += score_encoding_progress.exam_enrollments_encoded
        self.total_exam_enrollments += score_encoding_progress.total_exam_enrollments

    def increment_remaining_scores_by_deadline(self, score_encoding_progress):
        for deadline_computed, scores_not_yet_submitted in score_encoding_progress.remaining_scores_by_deadline.items():
            if deadline_computed in self.remaining_scores_by_deadline:
                self.remaining_scores_by_deadline[deadline_computed] += scores_not_yet_submitted
            else:
                self.remaining_scores_by_deadline[deadline_computed] = scores_not_yet_submitted
