##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import csv
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as trans
from base import models as mdl
from base.utils import send_mail, pdf_utils, export_utils
from . import layout
import json
import datetime


def _is_inside_scores_encodings_period(user):
    """
    :param user: The request.User
    :return: True if the today date is inside a period of scores encodings (inside session 1,2 or 3). Else return False.
    """
    now = datetime.datetime.now().date()
    academic_calendars = list(mdl.academic_calendar.get_scores_encoding_calendars())
    for ac_calendar in academic_calendars:
        if ac_calendar.start_date and ac_calendar.end_date:
            if ac_calendar.start_date <= now <= ac_calendar.end_date:
                return True
    return False


@login_required
def outside_scores_encodings_period(request):
    now = datetime.datetime.now().date()
    academic_calendars = list(mdl.academic_calendar.get_scores_encoding_calendars())
    last_academic_calendar = None
    # Searching for the latest period of scores encodings
    for ac_calendar in academic_calendars:
        if ac_calendar.start_date and ac_calendar.end_date:
            if last_academic_calendar is None:
                last_academic_calendar = ac_calendar
            elif now - ac_calendar.end_date < now - last_academic_calendar.end_date:
                last_academic_calendar = ac_calendar

    str_date = last_academic_calendar.end_date.strftime('%d/%m/%Y') if last_academic_calendar else ''
    text = trans('outside_scores_encodings_period') % str_date
    messages.add_message(request, messages.WARNING, "%s" % text)
    return layout.render(request, "assessments/outside_scores_encodings_period.html", {})


def _truncate_decimals(new_score, new_justification, decimal_scores_authorized):
    """
    Truncate decimals of new scores if decimals are unauthorized.
    :param new_score:
    :param new_justification:
    :return:
    """
    if new_score is not None:
        new_score = new_score.strip().replace(',', '.')
        if new_score == '':
            new_score = None
        else:
            if decimal_scores_authorized:
                new_score = float(new_score)
            else:
                new_score = int(float(new_score))
    if new_justification == '':
        new_justification = None
    return new_score, new_justification


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def scores_encoding(request):
    # In case the user is a program manager
    if mdl.program_manager.is_program_manager(user=request.user):
        return get_data_pgmer(request)

    # In case the user is a Tutor
    elif mdl.tutor.is_tutor(request.user):
        return get_data(request)
    else:
        return layout.render(request, "assessments/scores_encoding.html", {})


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def online_encoding(request, learning_unit_year_id=None):
    data_dict = get_data_online(learning_unit_year_id, request)
    return layout.render(request, "assessments/online_encoding.html", data_dict)


def __send_message_if_all_encoded_in_pgm(enrollments, learning_unit_year):
    """
    Send a message to all the tutors of a learning unit inside a program
    managed by the program manager if all the scores
    of this learning unit, inside this program, are encoded.
    Th encoder is a program manager, so all the encoded scores are final.
    :param enrollments: The enrollments to the learning unit year , inside the managed program.
    :param learning_unit_year: The lerning unit year of the enrollments.
    :param double : True if double encoding, else False
    :return: An error messaged if the message cannot be sent.
    """
    progress = mdl.exam_enrollment.calculate_exam_enrollment_progress(enrollments)
    offer_acronym = enrollments[0].learning_unit_enrollment.offer_enrollment.offer_year.acronym
    sent_error_message = None
    if progress == 100:
        persons = list(set([tutor.person for tutor
                            in mdl.tutor.find_by_learning_unit(learning_unit_year.learning_unit_id)]))
        sent_error_message = send_mail.send_message_after_all_encoded_by_manager(persons, enrollments,
                                                                                 learning_unit_year.acronym,
                                                                                 offer_acronym)
    return sent_error_message


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def online_encoding_form(request, learning_unit_year_id=None):
    data = get_data_online(learning_unit_year_id, request)

    if request.method == 'GET':
        return layout.render(request, "assessments/online_encoding_form.html", data)

    elif request.method == 'POST':
        decimal_scores_authorized = data['learning_unit_year'].decimal_scores
        for enrollment in data['enrollments']:
            score = request.POST.get('score_' + str(enrollment.id), None)
            justification = request.POST.get('justification_' + str(enrollment.id), None)
            score_changed = request.POST.get('score_changed_' + str(enrollment.id), 'false')

            # modification is possible for program managers OR score has changed but nothing is final
            if data['is_program_manager'] or \
                    score_changed == 'true' and \
                    enrollment.score_final is None and not enrollment.justification_final:

                new_score, new_justification = _truncate_decimals(score, justification, decimal_scores_authorized)
                enrollment.score_reencoded = None
                enrollment.justification_reencoded = None

                # draft score and justification are always set
                enrollment.score_draft = new_score
                enrollment.justification_draft = new_justification
                # it is only the program manager who validates the double encoding
                if data['is_program_manager']:
                    enrollment.score_final = new_score
                    enrollment.justification_final = new_justification
                    mdl.exam_enrollment.create_exam_enrollment_historic(request.user, enrollment,
                                                                        enrollment.score_final,
                                                                        enrollment.justification_final)
                enrollment.save()

        data = get_data_online(learning_unit_year_id, request)
        if data['is_program_manager']:
            sent_error_message = __send_message_if_all_encoded_in_pgm(data.get('enrollments'),
                                                                      data.get('learning_unit_year'))
            if sent_error_message:
                messages.add_message(request, messages.ERROR, "%s" % sent_error_message)
        return layout.render(request, "assessments/online_encoding.html", data)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def online_double_encoding_form(request, learning_unit_year_id=None):
    data = get_data_online_double(learning_unit_year_id, request)
    encoded_exam_enrollments = data['enrollments']

    # Case asking for a double encoding
    if request.method == 'GET':
        if len(encoded_exam_enrollments) > 0:
            return layout.render(request, "assessments/online_double_encoding_form.html", data)
        else:
            messages.add_message(request, messages.WARNING, "%s" % _('no_score_encoded_double_encoding_impossible'))
            return online_encoding(request, learning_unit_year_id=learning_unit_year_id)

    # Case asking for a comparison with scores double encoded
    elif request.method == 'POST':
        decimal_scores_authorized = data['learning_unit_year'].decimal_scores

        # Clean double encoded scores before dealing with a new double encoding.
        reencoded_exam_enrollments = []
        for enrollment in encoded_exam_enrollments:
            score_changed = request.POST.get('score_changed_' + str(enrollment.id), 'false')
            if score_changed == 'true':
                reencoded_exam_enrollments.append(enrollment)

        for enrollment in reencoded_exam_enrollments:
            score_double_encoded = request.POST.get('score_' + str(enrollment.id), None)

            justification_double_encoded = request.POST.get('justification_' + str(enrollment.id), None)
            score_double_encoded, justification_double_encoded = _truncate_decimals(score_double_encoded,
                                                                                    justification_double_encoded,
                                                                                    decimal_scores_authorized)
            enrollment.score_reencoded = score_double_encoded
            enrollment.justification_reencoded = justification_double_encoded
            enrollment.save()

        # Needs to filter by examEnrollments where the score_reencoded and justification_reencoded are not None
        # encoded_exam_enrollments = [exam_enrol for exam_enrol in reencoded_exam_enrollments
        #                     if exam_enrol.score_reencoded is not None or exam_enrol.justification_reencoded]
        reencoded_exam_enrollments = mdl.exam_enrollment.sort_for_encodings(reencoded_exam_enrollments)
        data['enrollments'] = reencoded_exam_enrollments

        if len(reencoded_exam_enrollments) == 0:
            messages.add_message(request, messages.WARNING, "%s" % _('no_dubble_score_encoded_comparison_impossible'))
            return online_encoding(request, learning_unit_year_id=learning_unit_year_id)
        return layout.render(request, "assessments/online_double_encoding_validation.html", data)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def online_double_encoding_validation(request, learning_unit_year_id=None, tutor_id=None):
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    academic_year = mdl.academic_year.current_academic_year()
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             academic_year=academic_year,
                                             is_program_manager=is_program_manager)

    # Case the user validate his choice between the first and the double encoding
    if request.method == 'POST':
        # Needs to filter by examEnrollments where the score_reencoded and justification_reencoded are not None
        exam_enrollments_reencoded = [exam_enrol for exam_enrol in exam_enrollments
                                      if exam_enrol.score_reencoded is not None or exam_enrol.justification_reencoded]

        decimal_scores_authorized = learning_unit_year.decimal_scores

        for exam_enrol in exam_enrollments_reencoded:
            score_validated = request.POST.get('score_' + str(exam_enrol.id), None)
            justification_validated = request.POST.get('justification_' + str(exam_enrol.id), None)

            if score_validated is not None or justification_validated is not None:
                new_score, new_justification = _truncate_decimals(score_validated, justification_validated,
                                                                  decimal_scores_authorized)
                exam_enrol.score_reencoded = None
                exam_enrol.justification_reencoded = None

                # A choice must be done between the first and the double encoding to save new changes.
                if new_score is not None or new_justification:
                    # Case it is the program manager who validates the double encoding
                    if is_program_manager:
                        exam_enrol.score_draft = new_score
                        exam_enrol.score_final = new_score
                        exam_enrol.justification_draft = new_justification
                        exam_enrol.justification_final = new_justification
                        mdl.exam_enrollment.create_exam_enrollment_historic(request.user, exam_enrol,
                                                                            exam_enrol.score_final,
                                                                            exam_enrol.justification_final)
                    else:  # Case it is the tutor who validates the double encoding
                        exam_enrol.score_draft = new_score
                        exam_enrol.justification_draft = new_justification
                    exam_enrol.save()
        if is_program_manager:
            sent_error_message = __send_message_if_all_encoded_in_pgm(exam_enrollments, learning_unit_year)
            if sent_error_message:
                messages.add_message(request, messages.ERROR, "%s" % sent_error_message)
        return HttpResponseRedirect(reverse('online_encoding', args=(learning_unit_year_id,)))


def online_encoding_submission(request, learning_unit_year_id):
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             is_program_manager=is_program_manager)
    submitted_enrollments = []
    # contains all SessionExams where the encoding is not terminated (progression < 100%)
    sessions_exam_still_open = set()
    # contains all sessions exams in exam_enrollments list

    draft_scores_not_sumitted_yet = [exam_enrol for exam_enrol in exam_enrollments
                                     if (exam_enrol.justification_draft or exam_enrol.score_draft is not None) and
                                     not exam_enrol.justification_final and exam_enrol.score_final is None]
    for exam_enroll in draft_scores_not_sumitted_yet:
        if (exam_enroll.score_draft is not None and exam_enroll.score_final is None) \
                or (exam_enroll.justification_draft and not exam_enroll.justification_final):
            submitted_enrollments.append(exam_enroll)
        if exam_enroll.score_draft is not None or exam_enroll.justification_draft:
            if exam_enroll.score_draft is not None:
                exam_enroll.score_final = exam_enroll.score_draft
            if exam_enroll.justification_draft:
                exam_enroll.justification_final = exam_enroll.justification_draft
            exam_enroll.save()
            mdl.exam_enrollment.create_exam_enrollment_historic(request.user, exam_enroll,
                                                                exam_enroll.score_final,
                                                                exam_enroll.justification_final)

    # Send mail to all the teachers of the submitted learning unit on any submission
    all_encoded = len(sessions_exam_still_open) == 0
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    attributions = mdl.attribution.Attribution.objects.filter(learning_unit=learning_unit_year.learning_unit)
    persons = list(set([attribution.tutor.person for attribution in attributions]))
    sent_error_message = send_mail.send_mail_after_scores_submission(persons, learning_unit_year.acronym,
                                                                     submitted_enrollments, all_encoded)
    if sent_error_message:
        messages.add_message(request, messages.ERROR, "%s" % sent_error_message)
    return HttpResponseRedirect(reverse('online_encoding', args=(learning_unit_year_id,)))


@login_required
def upload_score_error(request):
    return layout.render(request, "assessments/upload_score_error.html", {})


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def notes_printing(request, learning_unit_year_id=None, tutor_id=None, offer_id=None):
    academic_year = mdl.academic_year.current_academic_year()
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             academic_year=academic_year,
                                             tutor_id=tutor_id,
                                             offer_year_id=offer_id,
                                             is_program_manager=is_program_manager)
    tutor = mdl.tutor.find_by_user(request.user) if not is_program_manager else None
    return pdf_utils.print_notes(exam_enrollments, tutor=tutor)


@login_required
def notes_printing_all(request, tutor_id=None, offer_id=None):
    return notes_printing(request, tutor_id=tutor_id, offer_id=offer_id)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def export_xls(request, learning_unit_year_id, academic_year_id):
    academic_year = mdl.academic_year.current_academic_year()
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             academic_year=academic_year,
                                             is_program_manager=is_program_manager)
    return export_utils.export_xls(academic_year_id, is_program_manager, exam_enrollments)


def get_score_encoded(enrollments):
    progress = 0
    if enrollments:
        for e in enrollments:
            if e.score_final is not None or e.justification_final:
                progress += 1
    return progress


def get_data(request, offer_year_id=None):
    offer_year_id = int(offer_year_id) if offer_year_id else None
    academic_yr = mdl.academic_year.current_academic_year()
    tutor = mdl.attribution.get_assigned_tutor(request.user)
    exam_enrollments = list(mdl.exam_enrollment.find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                         tutor=tutor))

    all_offers = []
    for exam_enrol in exam_enrollments:
        off_year = exam_enrol.learning_unit_enrollment.offer_enrollment.offer_year
        if off_year not in all_offers:
            all_offers.append(off_year)
    all_offers = sorted(all_offers, key=lambda k: k.acronym)

    if offer_year_id:
        exam_enrollments = [exam_enrol for exam_enrol in exam_enrollments
                            if exam_enrol.learning_unit_enrollment.offer_enrollment.offer_year.id == offer_year_id]
    # Grouping by learningUnitYear
    group_by_learn_unit_year = {}
    for exam_enrol in exam_enrollments:
        learn_unit_year = exam_enrol.session_exam.learning_unit_year
        score_encoding = group_by_learn_unit_year.get(learn_unit_year.id)
        if score_encoding:
            if exam_enrol.score_final is not None or exam_enrol.justification_final:
                score_encoding['exam_enrollments_encoded'] += 1
            score_encoding['total_exam_enrollments'] += 1
        else:
            if exam_enrol.score_final is not None or exam_enrol.justification_final:
                exam_enrollments_encoded = 1
            else:
                exam_enrollments_encoded = 0
            group_by_learn_unit_year[learn_unit_year.id] = {'learning_unit_year': learn_unit_year,
                                                            'exam_enrollments_encoded': exam_enrollments_encoded,
                                                            'total_exam_enrollments': 1}
    scores_list = group_by_learn_unit_year.values()
    # Adding progress for each line (progress by learningUnitYear)
    for exam_enrol_by_learn_unit in scores_list:
        progress = (exam_enrol_by_learn_unit['exam_enrollments_encoded']
                    / exam_enrol_by_learn_unit['total_exam_enrollments']) * 100
        exam_enrol_by_learn_unit['progress'] = "{0:.0f}".format(progress)
        exam_enrol_by_learn_unit['progress_int'] = progress
    # Filtering by learningUnitYear.acronym
    scores_list = sorted(scores_list, key=lambda k: k['learning_unit_year'].acronym)

    return layout.render(request, "assessments/scores_encoding.html",
                         {'tutor': tutor,
                          'academic_year': academic_yr,
                          'notes_list': scores_list,
                          'number_session': mdl.session_exam.find_session_exam_number(),
                          'offer_year_list': all_offers,
                          'offer_year_id': offer_year_id})


def get_data_online(learning_unit_year_id, request):
    """
    Args:
        learning_unit_year_id: The id of an annual learning unit.
        request: default http request.
    Returns:
        a reusable map used by several templates to show data on the user interface.
    """
    academic_yr = mdl.academic_year.current_academic_year()
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             academic_year=academic_yr,
                                             is_program_manager=is_program_manager)

    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)

    coordinator = mdl.attribution.find_responsible(learning_unit_year.learning_unit)
    progress = mdl.exam_enrollment.calculate_exam_enrollment_progress(exam_enrollments)

    draft_scores_not_submitted = len([exam_enrol for exam_enrol in exam_enrollments
                                     if (exam_enrol.justification_draft or exam_enrol.score_draft is not None) and
                                        (not exam_enrol.justification_final and exam_enrol.score_final is None)])
    return {'section': 'scores_encoding',
            'academic_year': academic_yr,
            'progress': "{0:.0f}".format(progress),
            'progress_int': progress,
            'enrollments': exam_enrollments,
            'learning_unit_year': learning_unit_year,
            'coordinator': coordinator,
            'is_program_manager': is_program_manager,
            'is_coordinator': mdl.attribution.is_coordinator(request.user, learning_unit_year.learning_unit.id),
            'draft_scores_not_submitted': draft_scores_not_submitted,
            'number_session': exam_enrollments[0].session_exam.number_session if len(exam_enrollments) > 0 else _('none'),
            'tutors': mdl.tutor.find_by_learning_unit(learning_unit_year.learning_unit_id),
            'exam_enrollments_encoded': len([e for e in exam_enrollments if e.score_final is not None or e.justification_final]),
            'total_exam_enrollments': len(exam_enrollments)}


def get_data_online_double(learning_unit_year_id, request):
    academic_yr = mdl.academic_year.current_academic_year()
    if mdl.program_manager.is_program_manager(request.user):
        offer_years_managed = mdl.offer_year.find_by_user(request.user, academic_yr=academic_yr)
        total_exam_enrollments = list(mdl.exam_enrollment
                                      .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                learning_unit_year_id=learning_unit_year_id,
                                                                offers_year=offer_years_managed))
        # We must know the total count of enrollments (not only the encoded one)
        encoded_exam_enrollments = [enrollment for enrollment in total_exam_enrollments
                                    if enrollment.justification_final or enrollment.score_final is not None]
    elif mdl.tutor.is_tutor(request.user):
        total_exam_enrollments = list(mdl.exam_enrollment
                                      .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                learning_unit_year_id=learning_unit_year_id))
        encoded_exam_enrollments = [enrollment for enrollment in total_exam_enrollments if
                                    (enrollment.justification_draft or enrollment.score_draft is not None) and not
                                    enrollment.justification_final and enrollment.score_final is None]
    else:
        encoded_exam_enrollments = []
        total_exam_enrollments = []
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)

    nb_final_scores = len([exam_enrol for exam_enrol in encoded_exam_enrollments
                          if exam_enrol.justification_final or exam_enrol.score_final is not None])
    coordinator = mdl.attribution.find_responsible(learning_unit_year.learning_unit)

    encoded_exam_enrollments = mdl.exam_enrollment.sort_for_encodings(encoded_exam_enrollments)

    return {'section': 'scores_encoding',
            'academic_year': academic_yr,
            'enrollments': encoded_exam_enrollments,
            'num_encoded_scores': nb_final_scores,
            'learning_unit_year': learning_unit_year,
            'justifications': mdl.exam_enrollment.JUSTIFICATION_TYPES,
            'is_program_manager': mdl.program_manager.is_program_manager(request.user),
            'coordinator': coordinator,
            'count_total_enrollments': len(total_exam_enrollments),
            'number_session': encoded_exam_enrollments[0].session_exam.number_session
                              if len(encoded_exam_enrollments) > 0 else _('none'),
            'tutors': mdl.tutor.find_by_learning_unit(learning_unit_year.learning_unit_id)}


def get_data_pgmer(request,
                   offer_year_id=None,
                   tutor_id=None,
                   learning_unit_year_acronym=None,
                   incomplete_encodings_only=False):
    NOBODY = -1
    academic_yr = mdl.academic_year.current_academic_year()
    learning_unit_year_ids = None
    if learning_unit_year_acronym:
        learning_unit_year_ids = mdl.learning_unit_year.search(acronym=learning_unit_year_acronym).values_list('id',
                                                                                                               flat=True)

    if not offer_year_id:
        scores_encodings = list(mdl.scores_encoding.search(request.user, learning_unit_year_ids=learning_unit_year_ids))
        # Adding exam_enrollments_encoded & total_exam_enrollments
        # from each offers year for a matching learning_unit_year
        group_by_learning_unit = {}
        for score_encoding in scores_encodings:
            try:
                group_by_learning_unit[score_encoding.learning_unit_year_id].exam_enrollments_encoded\
                    += score_encoding.exam_enrollments_encoded
                group_by_learning_unit[score_encoding.learning_unit_year_id].total_exam_enrollments\
                    += score_encoding.total_exam_enrollments
            except KeyError:
                group_by_learning_unit[score_encoding.learning_unit_year_id] = score_encoding
        scores_encodings = group_by_learning_unit.values()
    else:
        # Filter list by offer_year
        offer_year_id = int(offer_year_id)  # The offer_year_id received in session is a String, not an Int
        scores_encodings = list(mdl.scores_encoding.search(request.user,
                                                           offer_year_id=offer_year_id,
                                                           learning_unit_year_ids=learning_unit_year_ids))
        scores_encodings = [score_encoding for score_encoding in scores_encodings
                            if score_encoding.offer_year_id == offer_year_id]

    if tutor_id:
        # Filter list by tutor
        # The tutor_id received in session is a String, not an Int
        tutor_id = int(tutor_id)
        # NOBODY (-1) in case to filter by learningUnit without attribution. In this case,
        # the list is filtered after retrieved
        # all data and tutors below
        if tutor_id != NOBODY:
            tutor = mdl.tutor.find_by_id(tutor_id)
            learning_unit_ids_by_tutor = set(mdl.attribution.search(tutor=tutor).values_list('learning_unit', flat=True))
            # learning_unit_ids_attrib = [attr.learning_unit.id for attr in attributions_by_tutor]
            scores_encodings = [score_encoding for score_encoding in scores_encodings
                                if score_encoding.learning_unit_year.learning_unit.id in learning_unit_ids_by_tutor]

    data = []
    all_attributions = []
    if scores_encodings:  # Empty in case there isn't any score to encode (not inside the period of scores' encoding)
        # Adding coordinator for each learningUnit
        learning_unit_ids = [score_encoding.learning_unit_year.learning_unit.id for score_encoding in scores_encodings]
        all_attributions = list(mdl.attribution.search(learning_unit_ids=learning_unit_ids))
        coord_grouped_by_learning_unit = {attrib.learning_unit.id: attrib.tutor for attrib in all_attributions
                                          if attrib.function == 'COORDINATOR'}
        for score_encoding in scores_encodings:
            progress = (score_encoding.exam_enrollments_encoded / score_encoding.total_exam_enrollments) * 100
            line = {}
            line['learning_unit_year'] = score_encoding.learning_unit_year
            line['exam_enrollments_encoded'] = score_encoding.exam_enrollments_encoded
            line['total_exam_enrollments'] = score_encoding.total_exam_enrollments
            line['tutor'] = coord_grouped_by_learning_unit.get(score_encoding.learning_unit_year.learning_unit.id,
                                                               None)
            line['progress'] = "{0:.0f}".format(progress)
            line['progress_int'] = progress
            data.append(line)

    if incomplete_encodings_only:
        # Filter by completed encodings (100% complete)
        data = [line for line in data if line['exam_enrollments_encoded'] != line['total_exam_enrollments']]

    if tutor_id == NOBODY: # LearningUnit without attribution
        data = [line for line in data if line['tutor'] is None]

    # Creating list of all tutors
    all_tutors = []
    # all_tutors.append({'id': NOBODY, 'last_name': 'NOBODY', 'first_name': ''})
    for attrib in all_attributions:
        tutor = attrib.tutor
        if tutor and tutor not in all_tutors:
            all_tutors.append(tutor)
    all_tutors = sorted(all_tutors, key=lambda k: k.person.last_name.upper() if k.person.last_name else ''
                                                + k.person.first_name.upper() if k.person.first_name else '')

    # Creating list of offer Years for the filter (offers year with minimum 1 record)
    all_offers = mdl.offer_year.find_by_user(request.user, academic_yr=academic_yr)

    # Ordering by learning_unit_year.acronym
    data = sorted(data, key=lambda k: k['learning_unit_year'].acronym)

    if len(data) == 0:
        messages.add_message(request, messages.WARNING, "%s" % _('no_result'))

    return layout.render(request, "assessments/scores_encoding_by_learning_unit.html",
                         {'notes_list': data,
                          'offer_list': all_offers,
                          'tutor_list': all_tutors,
                          'offer_year_id': offer_year_id,
                          'tutor_id': tutor_id,
                          'academic_year': academic_yr,
                          'number_session': mdl.session_exam.find_session_exam_number(),
                          'learning_unit_year_acronym': learning_unit_year_acronym,
                          'incomplete_encodings_only': incomplete_encodings_only})


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
def refresh_list(request):
    # In case the user is a program manager
    if mdl.program_manager.is_program_manager(user=request.user):
        return get_data_pgmer(request,
                              offer_year_id=request.GET.get('offer', None),
                              tutor_id=request.GET.get('tutor', None),
                              learning_unit_year_acronym=request.GET.get('learning_unit_year_acronym', None),
                              incomplete_encodings_only=request.GET.get('incomplete_encodings_only', False))

    # In case the user is a Tutor
    else:
        return get_data(request, offer_year_id=request.GET.get('offer_year_id', None))


def get_data_specific_criteria(request):
    registration_id = request.POST.get('registration_id', None)
    last_name = request.POST.get('last_name', None)
    first_name = request.POST.get('first_name', None)
    justification = request.POST.get('justification', None)
    offer_year_id = request.POST.get('program', None)

    academic_yr = mdl.academic_year.current_academic_year()
    number_session = mdl.session_exam.find_session_exam_number()

    offers_year_managed = mdl.offer_year.find_by_user(request.user, academic_yr)

    is_program_manager = mdl.program_manager.is_program_manager(request.user)

    exam_enrollments = []

    if request.method == 'POST':
        if is_program_manager:
            if not registration_id and not last_name and not first_name and not justification and not offer_year_id:
                messages.add_message(request, messages.WARNING, "%s" % _('minimum_one_criteria'))
            else:
                offer_year_id = int(
                    offer_year_id) if offer_year_id else None  # The offer_year_id received in session is a String, not an Int
                exam_enrollments = list(mdl.exam_enrollment.find_for_score_encodings(number_session,
                                                                                     registration_id=registration_id,
                                                                                     student_last_name=last_name,
                                                                                     student_first_name=first_name,
                                                                                     justification=justification,
                                                                                     offer_year_id=offer_year_id,
                                                                                     offers_year=offers_year_managed))
                exam_enrollments = mdl.exam_enrollment.sort_by_last_name_first_name(exam_enrollments)
                if len(exam_enrollments) == 0:
                    messages.add_message(request, messages.WARNING, "%s" % _('no_result'))
        else:
            messages.add_message(request, messages.ERROR, "%s" % _('user_is_not_program_manager'))
    return {'offer_year_id': offer_year_id,
            'registration_id': registration_id,
            'last_name': last_name,
            'first_name': first_name,
            'justification': justification,
            'academic_year': academic_yr,
            'offer_list': offers_year_managed,
            'number_session': number_session,
            'exam_enrollments': exam_enrollments,
            'is_program_manager': is_program_manager}


@login_required
def specific_criteria(request):
    data = get_data_specific_criteria(request)
    return layout.render(request, "assessments/scores_encoding_by_specific_criteria.html", data)


@login_required
def search_by_specific_criteria(request):
    return specific_criteria(request)


@login_required
def specific_criteria_submission(request):
    data = get_data_specific_criteria(request)

    scores_saved = 0

    learning_unit_years_changed = []

    for enrollment in data['exam_enrollments']:
        learning_unit_year = enrollment.learning_unit_enrollment.learning_unit_year
        decimal_scores_authorized = learning_unit_year.decimal_scores
        score = request.POST.get('score_' + str(enrollment.id), None)
        justification = request.POST.get('justification_' + str(enrollment.id), None)
        score_changed = request.POST.get('score_changed_' + str(enrollment.id), 'false')
        if score_changed == 'true':
            changed = True
        else:
            changed = False

        if changed:
            scores_saved += 1

            if learning_unit_year not in learning_unit_years_changed:
                learning_unit_years_changed.append(learning_unit_year)

            new_score, new_justification = _truncate_decimals(score, justification, decimal_scores_authorized)

            enrollment.score_draft = new_score
            enrollment.score_final = new_score
            enrollment.justification_draft = new_justification
            enrollment.justification_final = new_justification
            mdl.exam_enrollment.create_exam_enrollment_historic(request.user, enrollment,
                                                                enrollment.score_final,
                                                                enrollment.justification_final)
            enrollment.save()

    academic_yr = mdl.academic_year.current_academic_year()
    offers_year_managed = mdl.offer_year.find_by_user(request.user, academic_yr)
    all_exam_enrollments = list(mdl.exam_enrollment.find_for_score_encodings(session_exam_number=mdl.session_exam.find_session_exam_number(),
                                                                             offers_year=offers_year_managed,
                                                                             learning_unit_year_ids=[learn_unit_year.id for learn_unit_year in learning_unit_years_changed]))

    # ExamEnrollments by learning_unit_year (only if examEnrollment of the learningUnitYear has changed)
    grouped_by_learning_unit_years_for_mails = {}
    for enrollment in all_exam_enrollments:
        learning_unit_year = enrollment.learning_unit_enrollment.learning_unit_year
        if learning_unit_year in learning_unit_years_changed:
            if learning_unit_year in grouped_by_learning_unit_years_for_mails.keys():
                grouped_by_learning_unit_years_for_mails[learning_unit_year].append(enrollment)
            else:
                grouped_by_learning_unit_years_for_mails[learning_unit_year] = [enrollment]

    for learn_unit_year, exam_enrollments in grouped_by_learning_unit_years_for_mails.items():
        sent_error_message = __send_message_if_all_encoded_in_pgm(exam_enrollments,
                                                                  learn_unit_year)
        if sent_error_message:
            messages.add_message(request, messages.ERROR, "%s" % sent_error_message)

    messages.add_message(request, messages.INFO, "%s %s" % (scores_saved, _('scores_saved')))
    return specific_criteria(request)


def _get_exam_enrollments(user, learning_unit_year_id=None, tutor_id=None, offer_year_id=None, academic_year=None,
                          is_program_manager=False):
    """
    Args:
        user: The user who's asking for exam_enrollments (for scores' encoding).
        learning_unit_year_id: To filter ExamEnroll by learning_unit_year.
        tutor_id: To filter ExamEnroll by tutor.
        offer_year_id: To filter ExamEnroll by OfferYear.
        academic_year: The academic year for the data returned.
    Returns:
        All exam enrollments for the user passed in parameter (check if it is a program manager or a tutor) and
        a Boolean is_program_manager (True if the user is a program manager, False if the user is a Tutor/coord).
    """
    if not academic_year:
        academic_year = mdl.academic_year.current_academic_year()
    # Case the user is a program manager
    if is_program_manager:
        tutor = None
        if tutor_id:
            tutor = mdl.tutor.find_by_id(tutor_id)
        if offer_year_id:
            # Get examEnrollments for only one offer
            offers_year = [mdl.offer_year.find_by_id(offer_year_id)]
        else:
            # Get examEnrollments for all offers managed by the program manager
            offers_year = list(mdl.offer_year.find_by_user(user, academic_yr=academic_year))
        exam_enrollments = list(mdl.exam_enrollment
                                .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                          learning_unit_year_id=learning_unit_year_id,
                                                          tutor=tutor,
                                                          offers_year=offers_year))
    # Case the user is a tutor
    elif mdl.tutor.is_tutor(user):
        # Note : The tutor can't filter by offerYear ; the offer_id is always None. Not necessary to check.
        tutor = mdl.tutor.find_by_user(user)
        exam_enrollments = list(mdl.exam_enrollment
                                .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                          learning_unit_year_id=learning_unit_year_id,
                                                          tutor=tutor))
    else:
        exam_enrollments = []
    # Ordering by offerear.acronym, then person.lastname & firstname
    exam_enrollments = mdl.exam_enrollment.sort_for_encodings(exam_enrollments)
    return exam_enrollments


# To be removed once all program managers are imported.
def load_program_managers():
    with open('base/views/program-managers.csv') as csvfile:
        row = csv.reader(csvfile)
        imported_counter = 0
        error_counter = 0
        duplication_counter = 0
        for columns in row:
            if len(columns) > 0:
                offer_year = mdl.offer_year.find_by_acronym(columns[0].strip())
                person = mdl.person.find_by_global_id(columns[2].strip())

                if offer_year and person:
                    program_manager = mdl.program_manager.ProgramManager()
                    program_manager.offer_year = offer_year
                    program_manager.person = person
                    try:
                        program_manager.save()
                    except IntegrityError:
                        print('Duplicated : %s - %s' % (offer_year, person))
                        duplication_counter += 1
                    imported_counter += 1
                else:
                    error_counter += 1
                    print(u'"%s", "%s", "%s", "%s", "%s"' % (columns[0], columns[1], columns[2], offer_year, person))
        print(u'%d program managers imported.' % imported_counter)
        print(u'%d program managers not imported.' % error_counter)
        print(u'%d program managers duplicated.' % duplication_counter)


def get_json_data_scores_sheets(tutor_global_id):
    person = mdl.person.find_by_global_id(tutor_global_id)
    tutor = mdl.tutor.find_by_person(person)
    if tutor:
        exam_enrollments = list(mdl.exam_enrollment.find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                             tutor=tutor))
        data = mdl.exam_enrollment.scores_sheet_data(exam_enrollments, tutor=tutor)
        return json.dumps(data)
    else:
        return json.dumps({})
