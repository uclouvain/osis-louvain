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
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from base import models as mdl
from base.utils import send_mail, pdf_utils, export_utils


@login_required
def scores_encoding(request):
    academic_yr = mdl.academic_year.current_academic_year()

    tutor = mdl.tutor.find_by_user(request.user)
    # In case the user is a tutor.
    faculties = []
    sessions_list = []
    if tutor:
        sessions = mdl.session_exam.find_sessions_by_tutor(tutor, academic_yr)
        sessions_list.append(sessions)
    # In case the user is not a tutor we check whether it is a program manager for the offer.
    else:
        program_mgr_list = mdl.program_manager.find_by_user(request.user)
        for program_mgr in program_mgr_list:
            if program_mgr.offer_year:
                sessions = mdl.session_exam.find_sessions_by_offer(program_mgr.offer_year, academic_yr)
                sessions_list.append(sessions)
                faculty = program_mgr.offer_year.structure
                faculties.append(faculty)

    # Calculate the progress of all courses of the tutor.
    all_enrollments = []
    session = None
    sessions_offer =[]
    if sessions_list:
        for sessions in sessions_list:
            for session in sessions:
                enrollments = list(mdl.exam_enrollment.find_exam_enrollments_by_session(session))
                if enrollments:
                    all_enrollments = all_enrollments + enrollments
                session.progress = mdl.exam_enrollment.calculate_session_exam_progress(session)
            session = sessions.first()
            sessions_offer.append(session)

    return render(request, "scores_encoding.html",
                  {'section':        'scores_encoding',
                   'tutor':          tutor,
                   'faculties':      faculties,
                   'academic_year':  academic_yr,
                   'sessions_list':  sessions_list,
                   'session':        session,
                   'sessions_offer': sessions_offer})


@login_required
def online_encoding(request, session_id):
    tutor = None
    program_mgr_list = mdl.program_manager.find_by_user(request.user)
    if not program_mgr_list:
        tutor = mdl.tutor.find_by_user(request.user)

    academic_year = mdl.academic_year.current_academic_year()
    session = mdl.session_exam.find_session_by_id(session_id)
    faculty = session.offer_year_calendar.offer_year.structure

    enrollments = mdl.exam_enrollment.find_exam_enrollments_by_session(session)
    progress = mdl.exam_enrollment.calculate_exam_enrollment_progress(enrollments)
    num_encoded_scores = mdl.exam_enrollment.count_encoded_scores(enrollments)

    return render(request, "online_encoding.html",
                  {'section': 'scores_encoding',
                   'tutor': tutor,
                   'faculty': faculty,
                   'academic_year': academic_year,
                   'session': session,
                   'progress': "{0:.0f}".format(progress),
                   'enrollments': enrollments,
                   'num_encoded_scores': num_encoded_scores})


@login_required
def online_encoding_form(request, session_id):
    session = mdl.session_exam.find_session_by_id(session_id)
    enrollments = mdl.exam_enrollment.find_exam_enrollments_by_session(session)
    if request.method == 'GET':
        tutor = mdl.tutor.find_by_user(request.user)
        academic_year = mdl.academic_year.current_academic_year()
        return render(request, "online_encoding_form.html",
                      {'section': 'scores_encoding',
                       'tutor': tutor,
                       'academic_year': academic_year,
                       'session': session,
                       'enrollments': enrollments,
                       'justifications': mdl.exam_enrollment.JUSTIFICATION_TYPES})
    elif request.method == 'POST':
        for enrollment in enrollments:
            score = request.POST.get('score_' + str(enrollment.id), None)
            if score:
                if enrollment.session_exam.learning_unit_year.decimal_scores:
                    enrollment.score_draft = float(score)
                else:
                    enrollment.score_draft = int(float(score))
            else:
                enrollment.score_draft = enrollment.score_final
            if request.POST.get('justification_' + str(enrollment.id), None) == "None":
                enrollment.justification_draft = None
            else:
                enrollment.justification_draft = request.POST.get('justification_' + str(enrollment.id), None)
            enrollment.save()
        return HttpResponseRedirect(reverse('online_encoding', args=(session_id,)))


@login_required
def online_double_encoding_form(request, session_id):
    session = mdl.session_exam.find_session_by_id(session_id)
    enrollments = mdl.exam_enrollment.find_exam_enrollments_drafts_by_session(session)
    if request.method == 'GET':
        tutor = mdl.tutor.find_by_user(request.user)
        academic_year = mdl.academic_year.current_academic_year()
        return render(request, "online_double_encoding_form.html",
                      {'section': 'scores_encoding',
                       'tutor': tutor,
                       'academic_year': academic_year,
                       'session': session,
                       'enrollments': enrollments,
                       'justifications': mdl.exam_enrollment.JUSTIFICATION_TYPES})
    elif request.method == 'POST':
        for enrollment in enrollments:
            score = request.POST.get('score_' + str(enrollment.id), None)
            if score:
                if enrollment.session_exam.learning_unit_year.decimal_scores:
                    enrollment.score_reencoded = float(score)
                else:
                    enrollment.score_reencoded = int(float(score))
            else:
                enrollment.score_reencoded = None
            if request.POST.get('justification_' + str(enrollment.id), None) == "None":
                justification = None
            else:
                justification = request.POST.get('justification_' + str(enrollment.id), None)
            if justification:
                enrollment.justification_reencoded = justification
            else:
                enrollment.justification_reencoded = None
            enrollment.save()
        return HttpResponseRedirect(reverse('online_double_encoding_validation', args=(session.id,)))


@login_required
def online_double_encoding_validation(request, session_id):
    session_exam = mdl.session_exam.find_session_by_id(session_id)
    if request.method == 'GET':
        tutor = mdl.tutor.find_by_user(request.user)
        academic_year = mdl.academic_year.current_academic_year()
        enrollments = mdl.exam_enrollment.find_exam_enrollments_to_validate_by_session(session_exam)
        return render(request, "online_double_encoding_validation.html",
                      {'section': 'scores_encoding',
                       'tutor': tutor,
                       'academic_year': academic_year,
                       'session': session_exam,
                       'enrollments': enrollments,
                       'justifications': mdl.exam_enrollment.JUSTIFICATION_TYPES})

    elif request.method == 'POST':
        enrollments = mdl.exam_enrollment.find_exam_enrollments_by_session(session_exam)

        for enrollment in enrollments:
            score = request.POST.get('score_' + str(enrollment.id), None)
            if score:
                if enrollment.session_exam.learning_unit_year.decimal_scores:
                    enrollment.score_final = float(score)
                else:
                    enrollment.score_final = int(float(score))
                enrollment.score_draft = enrollment.score_final
            enrollment.score_reencoded = None

            justification = request.POST.get('justification_' + str(enrollment.id), None)
            if justification:
                enrollment.justification_final = justification
                enrollment.justification_draft = enrollment.justification_final
            if score or justification:
                mdl.exam_enrollment.create_exam_enrollment_historic(request.user, enrollment, score, justification)
            enrollment.justification_reencoded = None
            enrollment.save()

        all_encoded = True
        for enrollment in enrollments:
            if not enrollment.score_final and not enrollment.justification_final:
                all_encoded = False

        if all_encoded:
            session_exam.status = 'CLOSED'
            session_exam.save()

        return HttpResponseRedirect(reverse('online_encoding', args=(session_id,)))


@login_required
def online_encoding_submission(request, session_id):
    session_exam = mdl.session_exam.find_session_by_id(session_id)
    enrollments = mdl.exam_enrollment.find_exam_enrollments_drafts_by_session(session_exam)
    all_encoded = True
    for enrollment in enrollments:
        if enrollment.score_draft or enrollment.justification_draft:
            if enrollment.score_draft:
                enrollment.score_final = enrollment.score_draft
            if enrollment.justification_draft:
                enrollment.justification_final = enrollment.justification_draft
            enrollment.save()
            mdl.exam_enrollment.create_exam_enrollment_historic(request.user, enrollment, enrollment.score_final,
                                                           enrollment.justification_final)
        else:
            all_encoded = False

    if all_encoded:
        session_exam.status = 'CLOSED'
        session_exam.save()

    # Send mail to all the teachers of the submitted learning unit on any submission
    learning_unit = session_exam.learning_unit_year.learning_unit
    attributions = mdl.attribution.Attribution.objects.filter(learning_unit=learning_unit)
    persons = [attribution.tutor.person for attribution in attributions if attribution.function == 'PROFESSOR']
    send_mail.send_mail_after_scores_submission(persons, learning_unit.acronym)

    return HttpResponseRedirect(reverse('online_encoding', args=(session_id,)))


@login_required
def notes_printing(request, session_exam_id, learning_unit_year_id):
    tutor = mdl.tutor.find_by_user(request.user)
    academic_year = mdl.academic_year.current_academic_year()
    session_exam = mdl.session_exam.find_session_by_id(session_exam_id)
    return pdf_utils.print_notes(request, tutor, academic_year, session_exam, learning_unit_year_id)


@login_required
def upload_score_error(request):
    return render(request, "upload_score_error.html", {})


@login_required
def notes_printing(request, session_exam_id, learning_unit_year_id):
    tutor = mdl.tutor.find_by_user(request.user)
    academic_year = mdl.academic_year.current_academic_year()
    session_exam = mdl.session_exam.find_session_by_id(session_exam_id)
    return pdf_utils.print_notes(request, tutor, academic_year, session_exam, learning_unit_year_id)


@login_required
def notes_printing_all(request, session_id):
    return notes_printing(request, session_id, -1)


@login_required
def export_xls(request, session_id, academic_year_id):
    return export_utils.export_xls(request, session_id, academic_year_id)
