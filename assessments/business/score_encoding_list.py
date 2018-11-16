##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import copy
from decimal import Decimal, Context, Inexact
import unicodedata

from django.db import transaction

from base.models import academic_year, session_exam_calendar, exam_enrollment, program_manager, tutor, offer_year, \
                        learning_unit_year
from base.models.enums import exam_enrollment_justification_type


def get_scores_encoding_list(user, **kwargs):
    current_academic_year = academic_year.current_academic_year()
    current_number_session = session_exam_calendar.find_session_exam_number()
    is_program_manager = program_manager.is_program_manager(user)
    learning_unit_year_id = kwargs.get('learning_unit_year_id')
    offer_year_id = kwargs.get('offer_year_id')
    tutor_id = kwargs.get('tutor_id')
    enrollments_ids = kwargs.get('enrollments_ids')

    if is_program_manager:
        professor = tutor.find_by_id(tutor_id) if tutor_id else None
        offers_year = [offer_year.find_by_id(offer_year_id)] if offer_year_id else \
                       list(offer_year.find_by_user(user, academic_yr=current_academic_year))

        enrollments = exam_enrollment.find_for_score_encodings(
            academic_year=current_academic_year,
            session_exam_number=current_number_session,
            learning_unit_year_id=learning_unit_year_id,
            tutor=professor,
            offers_year=offers_year,
            registration_id=kwargs.get('registration_id'),
            student_last_name=kwargs.get('student_last_name'),
            student_first_name=kwargs.get('student_first_name'),
            justification=kwargs.get('justification')
        )
    else:
        professor = tutor.find_by_user(user)
        enrollments = exam_enrollment.find_for_score_encodings(
            academic_year=current_academic_year,
            session_exam_number=current_number_session,
            learning_unit_year_id=learning_unit_year_id,
            tutor=professor)

    # Want a subset of exam enrollment list
    if enrollments_ids:
        enrollments = enrollments.filter(id__in=enrollments_ids)

    # Append deadline/deadline_tutor for each exam enrollments
    enrollments = _append_session_exam_deadline(list(enrollments))
    enrollments = sort_encodings(enrollments)

    return ScoresEncodingList(**{
        'academic_year': current_academic_year,
        'number_session': current_number_session,
        'learning_unit_year': learning_unit_year.get_by_id(learning_unit_year_id) if learning_unit_year_id else None,
        'enrollments': enrollments
    })


def _append_session_exam_deadline(enrollments):
    for enrollment in enrollments:
        enrollment.deadline = exam_enrollment.get_deadline(enrollment)
        enrollment.deadline_reached = exam_enrollment.is_deadline_reached(enrollment)
        enrollment.deadline_tutor_reached = exam_enrollment.is_deadline_tutor_reached(enrollment)
    return enrollments


def filter_without_closed_exam_enrollments(scores_encoding_list, is_program_manager=True):
    if is_program_manager:
        scores_encoding_list.enrollments = [enrollment for enrollment in scores_encoding_list.enrollments
                                            if not exam_enrollment.is_deadline_reached(enrollment)]
    else:
        scores_encoding_list.enrollments = [enrollment for enrollment in scores_encoding_list.enrollments
                                            if not exam_enrollment.is_deadline_tutor_reached(enrollment)]
    return scores_encoding_list


def find_related_registration_ids(scores_encoding_list):
    return {enrollment.learning_unit_enrollment.student.registration_id
            for enrollment in scores_encoding_list.enrollments}


def find_related_offer_years(scores_encoding_list):
    return {enrollment.learning_unit_enrollment.offer_enrollment.offer_year
            for enrollment in scores_encoding_list.enrollments}


def find_related_learning_unit_years(scores_encoding_list):
    return {enrollment.learning_unit_enrollment.learning_unit_year
            for enrollment in scores_encoding_list.enrollments}


def update_enrollments(scores_encoding_list, user):
    is_program_manager = program_manager.is_program_manager(user)
    updated_enrollments = []
    for enrollment in scores_encoding_list.enrollments:
        enrollment_updated = update_enrollment(enrollment, user, is_program_manager)
        if enrollment_updated:
            updated_enrollments.append(enrollment_updated)
    return updated_enrollments


def assign_encoded_to_reencoded_enrollments(scores_encoding_list):
    scores_encoding_list_assigned = []
    for enrollment in scores_encoding_list.enrollments:
        enrollment = clean_score_and_justification(enrollment)
        enrollment.score_reencoded = enrollment.score_encoded
        enrollment.justification_reencoded = enrollment.justification_encoded
        enrollment.full_clean()
        scores_encoding_list_assigned.append(enrollment)

    scores_encoding_list.enrollments = scores_encoding_list_assigned
    return scores_encoding_list


def update_enrollment(enrollment, user, is_program_manager=None):
    if is_program_manager is None:
        is_program_manager = program_manager.is_program_manager(user)

    enrollment = clean_score_and_justification(enrollment)

    if can_modify_exam_enrollment(enrollment, is_program_manager) and \
            is_enrollment_changed(enrollment, is_program_manager):

        with transaction.atomic():
            enrollment_updated = set_score_and_justification(enrollment, is_program_manager)

            if is_program_manager:
                exam_enrollment.create_exam_enrollment_historic(user, enrollment)

            return enrollment_updated
    return None


def clean_score_and_justification(enrollment):
    is_decimal_scores_authorized = enrollment.learning_unit_enrollment.learning_unit_year.decimal_scores

    cleaned_score = None
    if enrollment.score_encoded is not None and enrollment.score_encoded != "":
        cleaned_score = _convert_to_decimal(enrollment.score_encoded, is_decimal_scores_authorized)

    cleaned_justification = None if not enrollment.justification_encoded else enrollment.justification_encoded
    if enrollment.justification_encoded == exam_enrollment_justification_type.SCORE_MISSING:
        cleaned_justification = cleaned_score = None

    enrollment_cleaned = copy.deepcopy(enrollment)
    enrollment_cleaned.score_encoded = cleaned_score
    enrollment_cleaned.justification_encoded = cleaned_justification
    return enrollment_cleaned


def _convert_to_decimal(score, decimal_scores_authorized):
    decimal_score = _format_score_to_decimal(score)

    if decimal_scores_authorized:
        try:
            # Ensure that we cannot have more than 2 decimal
            return decimal_score.quantize(Decimal(10) ** -2, context=Context(traps=[Inexact]))
        except:
            raise ValueError("score_have_more_than_2_decimal_places")
    else:
        try:
            # Ensure that we cannot have no decimal
            return decimal_score.quantize(Decimal('1.'), context=Context(traps=[Inexact]))
        except:
            raise ValueError("decimal_score_not_allowed")


def _format_score_to_decimal(score):
    if isinstance(score, str):
        score = score.strip().replace(',', '.')
        _check_str_score_is_digit(score)
    return Decimal(str(score))


def _check_str_score_is_digit(score_str):
    if not score_str.replace('.', '').isdigit():  # Case not empty string but have alphabetic values
        raise ValueError("Scores must be between 0 and 20")


def is_enrollment_changed(enrollment, is_program_manager):
    if is_program_manager:
        return (enrollment.justification_final != enrollment.justification_encoded) or \
               (enrollment.score_final != enrollment.score_encoded)
    else:
        return (enrollment.justification_draft != enrollment.justification_encoded) or \
               (enrollment.score_draft != enrollment.score_encoded)


def can_modify_exam_enrollment(enrollment, is_program_manager):
    if is_program_manager:
        return not is_deadline_reached(enrollment)

    return not is_deadline_reached(enrollment, False) and \
           not enrollment.score_final and not enrollment.justification_final and \
           enrollment.justification_encoded != exam_enrollment_justification_type.ABSENCE_JUSTIFIED


def is_deadline_reached(enrollment, is_program_manager=True):
    if is_program_manager:
        return exam_enrollment.is_deadline_reached(enrollment)
    else:
        return exam_enrollment.is_deadline_tutor_reached(enrollment)


def set_score_and_justification(enrollment, is_program_manager):
    enrollment.score_reencoded = None
    enrollment.justification_reencoded = None
    enrollment.score_draft = enrollment.score_encoded
    enrollment.justification_draft = enrollment.justification_encoded
    if is_program_manager:
        enrollment.score_final = enrollment.score_encoded
        enrollment.justification_final = enrollment.justification_encoded

    #Validation
    enrollment.full_clean()
    enrollment.save()

    return enrollment


class ScoresEncodingList:
    def __init__(self, **kwargs):
        self.academic_year = kwargs.get('academic_year')
        self.number_session = kwargs.get('number_session')
        self.learning_unit_year = kwargs.get('learning_unit_year')
        self.enrollments = kwargs.get('enrollments')

    @property
    def progress_int(self):
        return exam_enrollment.calculate_exam_enrollment_progress(self.enrollments)

    @property
    def progress(self):
        return "{0:.0f}".format(self.progress_int)

    @property
    def enrollment_draft_not_submitted(self):
        return [enrollment for enrollment in self.enrollments if enrollment.is_draft and not enrollment.is_final]

    @property
    def enrollment_encoded(self):
        return list(filter(lambda e: e.is_final, self.enrollments))


def sort_encodings(exam_enrollments):
    """
    Sort the list by
     0. LearningUnitYear.acronym
     1. offerYear.acronym
     2. student.lastname
     3. sutdent.firstname
    :param exam_enrollments: List of examEnrollments to sort
    :return:
    """
    def _sort(key):
        learn_unit_acronym = key.learning_unit_enrollment.learning_unit_year.acronym
        off_enroll = key.learning_unit_enrollment.offer_enrollment
        acronym = off_enroll.offer_year.acronym
        last_name = off_enroll.student.person.last_name
        first_name = off_enroll.student.person.first_name
        last_name = _normalize_string(last_name) if last_name else None
        first_name = _normalize_string(first_name) if first_name else None
        return "%s %s %s %s" % (learn_unit_acronym if learn_unit_acronym else '',
                                acronym if acronym else '',
                                last_name.upper() if last_name else '',
                                first_name.upper() if first_name else '')

    return sorted(exam_enrollments, key=lambda k: _sort(k))


def _normalize_string(string):
    """
    Remove accents in the string passed in parameter.
    For example : 'é - è' ==> 'e - e'  //  'àç' ==> 'ac'
    :param string: The string to normalize.
    :return: The normalized string
    """
    string = string.replace(" ", "")
    return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))
