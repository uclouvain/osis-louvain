##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import traceback
from decimal import Decimal, Context, Inexact
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as trans
from psycopg2._psycopg import OperationalError as PsycopOperationalError, InterfaceError as  PsycopInterfaceError
from django.db.utils import OperationalError as DjangoOperationalError, InterfaceError as DjangoInterfaceError
from base import models as mdl
from assessments import models as mdl_assess
from base.enums.exam_enrollment_justification_type import JUSTIFICATION_TYPES
from attribution import models as mdl_attr
from osis_common.document import paper_sheet
from base.utils import send_mail
from assessments.views import export_utils
from base.views import layout
import json
from osis_common.models.queue_exception import QueueException
import logging
from django.conf import settings
from django.db import connection

logger = logging.getLogger(settings.DEFAULT_LOGGER)
queue_exception_logger = logging.getLogger(settings.QUEUE_EXCEPTION_LOGGER)


def _is_inside_scores_encodings_period(user):
    return mdl.session_exam.is_inside_score_encoding()


def _is_not_inside_scores_encodings_period(user):
    return not _is_inside_scores_encodings_period(user)


@login_required
@permission_required('base.can_access_evaluation', raise_exception=True)
def assessments(request):
    return layout.render(request, "assessments.html", {'section': 'assessments'})


@login_required
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
@user_passes_test(_is_not_inside_scores_encodings_period, login_url=reverse_lazy('scores_encoding'))
def outside_period(request):
    latest_session_exam = mdl.session_exam.get_latest_session_exam()
    if latest_session_exam:
        str_date = latest_session_exam.offer_year_calendar.academic_calendar.end_date.strftime('%d/%m/%Y')
    else:
        str_date = ""
    text = trans('outside_scores_encodings_period') % str_date
    messages.add_message(request, messages.WARNING, text)
    return layout.render(request, "outside_scores_encodings_period.html", {})


def _truncate_decimals_new(score, decimal_scores_authorized):
    score = score.strip().replace(',', '.')

    if not score.replace('.', '').isdigit():
        raise ValueError("scores_must_be_between_0_and_20")

    if decimal_scores_authorized:
        try:
            # Ensure that we cannot have more than 2 decimal
            return Decimal(score).quantize(Decimal(10) ** -2, context=Context(traps=[Inexact]))
        except:
            raise ValueError("score_have_more_than_2_decimal_places")
    else:
        try:
            return int(score)
        except:
            raise ValueError("decimal_score_not_allowed")


def _truncate_decimals(new_score, new_justification, decimal_scores_authorized):
    """
    Truncate decimals of new scores if decimals are unauthorized.
    """
    try:
        new_score = new_score.strip().replace(',', '.')
        new_score = float(new_score)
        if not decimal_scores_authorized:
            new_score = int(new_score)
    except:
        new_score = None
    return new_score, None if not new_justification else new_justification


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def scores_encoding(request):
    if mdl.program_manager.is_program_manager(request.user):
        # In case the user is a program manager
        return get_data_pgmer(request, offer_year_id=request.GET.get('offer', None),
                              tutor_id=request.GET.get('tutor', None),
                              learning_unit_year_acronym=request.GET.get('learning_unit_year_acronym', None),
                              incomplete_encodings_only=request.GET.get('incomplete_encodings_only', False))
    elif mdl.tutor.is_tutor(request.user):
        # In case the user is a Tutor
        return get_data(request, offer_year_id=request.GET.get('offer_year_id', None))
    return layout.render(request, "scores_encoding.html", {})


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def online_encoding(request, learning_unit_year_id=None):
    data_dict = get_data_online(learning_unit_year_id, request)
    return layout.render(request, "online_encoding.html", data_dict)


def __send_messages_for_each_offer_year(all_enrollments, learning_unit_year, updated_enrollments):
    """
    Send a message for each offer year to all the tutors of a learning unit inside a program
    managed by the program manager if all the scores
    of this learning unit, inside this program, are encoded and at most one score is newly encoded.
    Th encoder is a program manager, so all the encoded scores are final.
    :param enrollments: The enrollments to the learning unit year , inside the managed program.
    :param learning_unit_year: The learning unit year of the enrollments.
    :param updated_enrollments: list of exam enrollments objects which has been updated
    :return: A list of error message if message cannot be sent
    """
    sent_error_messages = []
    offer_years = get_offer_years_from_enrollments(updated_enrollments)
    for offer_year in offer_years:
        sent_error_message = __send_message_for_offer_year(all_enrollments, learning_unit_year,
                                                           offer_year)
        if sent_error_message:
            sent_error_messages.append(sent_error_message)
    return sent_error_messages


def get_offer_years_from_enrollments(enrollments):
    list_offer_years = [enrollment.learning_unit_enrollment.offer_enrollment.offer_year for enrollment in enrollments]
    return list(set(list_offer_years))


def __send_message_for_offer_year(all_enrollments, learning_unit_year, offer_year):
    enrollments = filter_enrollments_by_offer_year(all_enrollments, offer_year)
    progress = mdl.exam_enrollment.calculate_exam_enrollment_progress(enrollments)
    offer_acronym = offer_year.acronym
    sent_error_message = None
    if progress == 100:
        persons = list(set([tutor.person for tutor in mdl.tutor.find_by_learning_unit(learning_unit_year)]))
        sent_error_message = send_mail.send_message_after_all_encoded_by_manager(persons, enrollments,
                                                                                 learning_unit_year.acronym,
                                                                                 offer_acronym)
    return sent_error_message


def filter_enrollments_by_offer_year(enrollments, offer_year):
    filtered_enrollments = filter(
        lambda enrollment: enrollment.learning_unit_enrollment.offer_enrollment.offer_year == offer_year,
        enrollments
    )
    return list(filtered_enrollments)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def online_encoding_form(request, learning_unit_year_id=None):
    data = get_data_online(learning_unit_year_id, request)
    if request.method == 'GET':
        return layout.render(request, "online_encoding_form.html", data)
    elif request.method == 'POST':
        updated_enrollments = []
        encoded_exam_enrollments = data['enrollments']
        decimal_scores_authorized = data['learning_unit_year'].decimal_scores
        is_program_manager = data['is_program_manager']

        for enrollment in encoded_exam_enrollments:
            score_encoded = request.POST.get('score_' + str(enrollment.id))
            justification_encoded = request.POST.get('justification_' + str(enrollment.id))

            # Ignore all which are not changed
            is_score_changed = request.POST.get('score_changed_' + str(enrollment.id))
            if is_score_changed != 'true':
                continue

            if not score_encoded:
                score_encoded = None
            if not justification_encoded:
                justification_encoded = None

            # Try to convert str recevied to a INT / FLOAT [According to decimal authorized]
            if score_encoded:
                try:
                    score_encoded = _truncate_decimals_new(score_encoded, decimal_scores_authorized)
                except Exception as e:
                    messages.add_message(request, messages.ERROR, _(e.args[0]))
                    continue

            if is_program_manager and score_encoded == enrollment.score_final and \
                            justification_encoded == enrollment.justification_final:
                continue
            if not is_program_manager and score_encoded == enrollment.score_draft and \
                            justification_encoded == enrollment.justification_draft:
                continue

            # Modification is possible only for program managers OR score has changed but justification/score final is NONE
            if is_program_manager or (not enrollment.score_final and not enrollment.justification_final):
                try:
                    set_score_and_justification_for_exam_enrollment(is_program_manager, enrollment,
                                                                    justification_encoded,
                                                                    score_encoded, request.user)
                    updated_enrollments.append(enrollment)
                except ValidationError as e:
                    messages.add_message(request, messages.ERROR, _('scores_must_be_between_0_and_20'))

        if messages.get_messages(request):
            # Error case  [Preserve selection user experience]
            for enrollment in data['enrollments']:
                enrollment.score_draft = request.POST.get('score_' + str(enrollment.id))
                enrollment.justification_draft = request.POST.get('justification_' + str(enrollment.id))
                if is_program_manager:
                    enrollment.score_final = request.POST.get('score_' + str(enrollment.id))
                    enrollment.justification_final = request.POST.get('justification_' + str(enrollment.id))

            return layout.render(request, "online_encoding_form.html", data)
        else:
            data = get_data_online(learning_unit_year_id, request)
            send_messages_to_notify_encoding_progress(request, data["enrollments"], data["learning_unit_year"],
                                                      is_program_manager, updated_enrollments)
            return layout.render(request, "online_encoding.html", data)


def send_messages_to_notify_encoding_progress(request, all_enrollments, learning_unit_year, is_program_manager,
                                              updated_enrollments):
    if is_program_manager:
        sent_error_messages = __send_messages_for_each_offer_year(all_enrollments,
                                                                  learning_unit_year,
                                                                  updated_enrollments)
        for sent_error_message in sent_error_messages:
            messages.add_message(request, messages.ERROR, "%s" % sent_error_message)


def update_exam_enrollments(request, exam_enrollments, decimal_scores_authorized, is_program_manager):
    validation_error = None
    updated_enrollments = []
    for enrollment in exam_enrollments:
        try:
            is_updated = update_exam_enrollment(request, is_program_manager, decimal_scores_authorized, enrollment)
            if is_updated:
                updated_enrollments.append(enrollment)
        except ValidationError as e:
            validation_error = e
            pass

    if validation_error is not None:
        raise validation_error
    return updated_enrollments


def update_exam_enrollment(request, is_pgm, decimal_scores_authorized, enrollment):
    score = request.POST.get('score_' + str(enrollment.id), None)
    justification = request.POST.get('justification_' + str(enrollment.id), None)
    score_changed = request.POST.get('score_changed_' + str(enrollment.id), None)
    # modification is possible for program managers OR score has changed but nothing is final
    if is_pgm or is_legible_for_modifying_exam_enrollment(score_changed, enrollment):
        new_score, new_justification = _truncate_decimals(score, justification, decimal_scores_authorized)
        exam_enrollment_has_been_modified = has_modify_exam_enrollment(enrollment, new_score, new_justification)
        set_score_and_justification_for_exam_enrollment(is_pgm, enrollment, new_justification, new_score, request.user)

        if exam_enrollment_has_been_modified:
            return True

    return False


def set_score_and_justification_for_exam_enrollment(is_pgm, enrollment, new_justification, new_score, user):
    enrollment.score_reencoded = None
    enrollment.justification_reencoded = None
    enrollment.score_draft = new_score
    enrollment.justification_draft = new_justification

    if is_pgm:
        enrollment.score_final = new_score
        enrollment.justification_final = new_justification
        enrollment.full_clean()
        mdl.exam_enrollment.create_exam_enrollment_historic(user, enrollment,
                                                            enrollment.score_final,
                                                            enrollment.justification_final)
    enrollment.full_clean()
    enrollment.save()


def is_legible_for_modifying_exam_enrollment(score_changed, exam_enrollment):
    if score_changed is None:
        return not exam_enrollment.score_final and not exam_enrollment.justification_final
    return score_changed == "true" and not exam_enrollment.score_final and not exam_enrollment.justification_final


def has_modify_exam_enrollment(exam_enrollment, new_score, new_justification):
    return exam_enrollment.score_final != new_score or exam_enrollment.justification_final != new_justification


def online_double_encoding_get_form(request, data=None, learning_unit_year_id=None):
    if len(data['enrollments']) > 0:
        return layout.render(request, "online_double_encoding_form.html", data)
    else:
        messages.add_message(request, messages.WARNING, "%s" % _('no_score_encoded_double_encoding_impossible'))
        return online_encoding(request, learning_unit_year_id=learning_unit_year_id)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def online_double_encoding_form(request, learning_unit_year_id=None):
    data = get_data_online_double(learning_unit_year_id, request)

    if request.method == 'GET':
        return online_double_encoding_get_form(request, data, learning_unit_year_id)
    elif request.method == 'POST':
        validation_error = None
        encoded_exam_enrollments = data['enrollments']
        decimal_scores_authorized = data['learning_unit_year'].decimal_scores

        reencoded_exam_enrollments = []
        for enrollment in encoded_exam_enrollments:
            score_double_encoded = request.POST.get('score_' + str(enrollment.id))
            justification_double_encoded = request.POST.get('justification_' + str(enrollment.id))

            # Ignore all which are not changed
            is_score_changed = request.POST.get('score_changed_' + str(enrollment.id))
            if is_score_changed != 'true':
                continue

            if not score_double_encoded:
                score_double_encoded = None
            if not justification_double_encoded:
                justification_double_encoded = None

            # Try to convert str recevied to a INT / FLOAT [According to decimal authorized]
            if score_double_encoded:
                try:
                    score_double_encoded = _truncate_decimals_new(score_double_encoded, decimal_scores_authorized)
                except Exception as e:
                    messages.add_message(request, messages.ERROR, _(e.args[0]))
                    continue

            # Ignore those which are not modified
            if score_double_encoded == enrollment.score_reencoded and \
                            justification_double_encoded == enrollment.justification_reencoded:
                continue

            enrollment.score_reencoded = score_double_encoded
            enrollment.justification_reencoded = justification_double_encoded
            reencoded_exam_enrollments.append(enrollment)
            try:
                enrollment.full_clean()
            except ValidationError:
                messages.add_message(request, messages.ERROR, "%s" % _('scores_must_be_between_0_and_20'))

        if messages.get_messages(request):
            # Error case  [Preserve selection user experience]
            for enrollment in data['enrollments']:
                enrollment.post_score_encoded = request.POST.get('score_' + str(enrollment.id))
                enrollment.post_justification_encoded = request.POST.get('justification_' + str(enrollment.id))

            return online_double_encoding_get_form(request, data, learning_unit_year_id)
        elif not reencoded_exam_enrollments:
            messages.add_message(request, messages.WARNING, "%s" % _('no_dubble_score_encoded_comparison_impossible'))
            return online_encoding(request, learning_unit_year_id=learning_unit_year_id)
        else:
            # Save all value [Validation is OK]
            for enrollment in encoded_exam_enrollments:
                enrollment.save()
            data['enrollments'] = mdl.exam_enrollment.sort_for_encodings(reencoded_exam_enrollments)
            return layout.render(request, "online_double_encoding_validation.html", data)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
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
        try:
            updated_enrollments = update_exam_enrollments(request, exam_enrollments_reencoded,
                                                          decimal_scores_authorized,
                                                          is_program_manager)
            send_messages_to_notify_encoding_progress(request, exam_enrollments, learning_unit_year, is_program_manager,
                                                      updated_enrollments)
        except ValidationError:
            messages.add_message(request, messages.ERROR, "%s" % _('scores_must_be_between_0_and_20'))
        return HttpResponseRedirect(reverse('online_encoding', args=(learning_unit_year_id,)))


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def online_encoding_submission(request, learning_unit_year_id):
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             is_program_manager=is_program_manager)
    submitted_enrollments = []
    draft_scores_not_sumitted_yet = [exam_enrol for exam_enrol in exam_enrollments
                                     if exam_enrol.is_draft and not exam_enrol.is_final]
    not_submitted_enrollments = set([ex for ex in exam_enrollments if not ex.is_final])
    for exam_enroll in draft_scores_not_sumitted_yet:
        if (exam_enroll.score_draft is not None and exam_enroll.score_final is None) \
                or (exam_enroll.justification_draft and not exam_enroll.justification_final):
            submitted_enrollments.append(exam_enroll)
            not_submitted_enrollments.remove(exam_enroll)
        if exam_enroll.is_draft:
            if exam_enroll.score_draft is not None:
                exam_enroll.score_final = exam_enroll.score_draft
            if exam_enroll.justification_draft:
                exam_enroll.justification_final = exam_enroll.justification_draft
            exam_enroll.full_clean()
            exam_enroll.save()
            mdl.exam_enrollment.create_exam_enrollment_historic(request.user, exam_enroll,
                                                                exam_enroll.score_final,
                                                                exam_enroll.justification_final)

    # Send mail to all the teachers of the submitted learning unit on any submission
    all_encoded = len(not_submitted_enrollments) == 0
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    attributions = mdl_attr.attribution.Attribution.objects.filter(learning_unit_year=learning_unit_year)
    persons = list(set([attribution.tutor.person for attribution in attributions]))
    sent_error_message = send_mail.send_mail_after_scores_submission(persons, learning_unit_year.acronym,
                                                                     submitted_enrollments, all_encoded)
    if sent_error_message:
        messages.add_message(request, messages.ERROR, "%s" % sent_error_message)
    return HttpResponseRedirect(reverse('online_encoding', args=(learning_unit_year_id,)))


@login_required
def upload_score_error(request):
    return layout.render(request, "upload_score_error.html", {})


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
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
    sheet_data = mdl.exam_enrollment.scores_sheet_data(exam_enrollments, tutor=tutor)
    return paper_sheet.print_notes(sheet_data)


@login_required
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def notes_printing_all(request, tutor_id=None, offer_id=None):
    return notes_printing(request, tutor_id=tutor_id, offer_id=offer_id)


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def export_xls(request, learning_unit_year_id):
    academic_year = mdl.academic_year.current_academic_year()
    is_program_manager = mdl.program_manager.is_program_manager(request.user)
    exam_enrollments = _get_exam_enrollments(request.user,
                                             learning_unit_year_id=learning_unit_year_id,
                                             academic_year=academic_year,
                                             is_program_manager=is_program_manager)
    return export_utils.export_xls(exam_enrollments)


def get_score_encoded(enrollments):
    return len(list(filter(lambda e: e.is_final, enrollments)))


def get_data(request, offer_year_id=None):
    offer_year_id = int(offer_year_id) if offer_year_id else None
    academic_yr = mdl.academic_year.current_academic_year()
    tutor = mdl.tutor.find_by_user(request.user)
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
            if exam_enrol.is_final:
                score_encoding['exam_enrollments_encoded'] += 1
            score_encoding['total_exam_enrollments'] += 1
        else:
            if exam_enrol.is_final:
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

    return layout.render(request, "scores_encoding.html",
                         {'tutor': tutor,
                          'academic_year': academic_yr,
                          'notes_list': scores_list,
                          'number_session': mdl.session_exam.find_session_exam_number(),
                          'offer_year_list': all_offers,
                          'offer_year_id': offer_year_id,
                          'active_tab': request.GET.get('active_tab', None)  # Allow keep selection
                          })


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

    score_responsibles = mdl_attr.attribution.find_all_responsibles(learning_unit_year)
    tutors = mdl.tutor.find_by_learning_unit(learning_unit_year) \
        .exclude(id__in=[score_responsible.id for score_responsible in score_responsibles])

    progress = mdl.exam_enrollment.calculate_exam_enrollment_progress(exam_enrollments)

    draft_scores_not_submitted = len([exam_enrol for exam_enrol in exam_enrollments
                                      if exam_enrol.is_draft and not exam_enrol.is_final])
    return {'section': 'scores_encoding',
            'academic_year': academic_yr,
            'progress': "{0:.0f}".format(progress),
            'progress_int': progress,
            'enrollments': exam_enrollments,
            'learning_unit_year': learning_unit_year,
            'score_responsibles': score_responsibles,
            'is_program_manager': is_program_manager,
            'is_coordinator': mdl_attr.attribution.is_score_responsible(request.user, learning_unit_year),
            'draft_scores_not_submitted': draft_scores_not_submitted,
            'number_session': exam_enrollments[0].session_exam.number_session if len(exam_enrollments) > 0 else _(
                'none'),
            'tutors': tutors,
            'exam_enrollments_encoded': get_score_encoded(exam_enrollments),
            'total_exam_enrollments': len(exam_enrollments)}


def get_data_online_double(learning_unit_year_id, request):
    academic_yr = mdl.academic_year.current_academic_year()
    if mdl.program_manager.is_program_manager(request.user):
        offer_years_managed = mdl.offer_year.find_by_user(request.user, academic_yr=academic_yr)
        total_exam_enrollments = list(mdl.exam_enrollment
                                      .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                learning_unit_year_id=learning_unit_year_id,
                                                                offers_year=offer_years_managed))
        # We must know the total count of enrollments (not only the encoded one) ???
        encoded_exam_enrollments = list(filter(lambda e: e.is_final, total_exam_enrollments))
    elif mdl.tutor.is_tutor(request.user):
        total_exam_enrollments = list(mdl.exam_enrollment
                                      .find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                                learning_unit_year_id=learning_unit_year_id))
        encoded_exam_enrollments = list(filter(lambda e: e.is_draft and not e.is_final, total_exam_enrollments))
    else:
        encoded_exam_enrollments = []
        total_exam_enrollments = []
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)

    nb_final_scores = get_score_encoded(encoded_exam_enrollments)
    score_responsibles = mdl_attr.attribution.find_all_responsibles(learning_unit_year)
    tutors = mdl.tutor.find_by_learning_unit(learning_unit_year) \
        .exclude(id__in=[score_responsible.id for score_responsible in score_responsibles])
    encoded_exam_enrollments = mdl.exam_enrollment.sort_for_encodings(encoded_exam_enrollments)

    return {'section': 'scores_encoding',
            'academic_year': academic_yr,
            'enrollments': encoded_exam_enrollments,
            'num_encoded_scores': nb_final_scores,
            'learning_unit_year': learning_unit_year,
            'justifications': JUSTIFICATION_TYPES,
            'is_program_manager': mdl.program_manager.is_program_manager(request.user),
            'score_responsibles': score_responsibles,
            'count_total_enrollments': len(total_exam_enrollments),
            'number_session': encoded_exam_enrollments[0].session_exam.number_session
            if len(encoded_exam_enrollments) > 0 else _('none'),
            'tutors': tutors}


def get_data_pgmer(request,
                   offer_year_id=None,
                   tutor_id=None,
                   learning_unit_year_acronym=None,
                   incomplete_encodings_only=False):
    NOBODY = -1
    academic_yr = mdl.academic_year.current_academic_year()
    learning_unit_year_ids = None
    if learning_unit_year_acronym:
        learning_unit_year_ids = mdl.learning_unit_year.search(acronym=learning_unit_year_acronym) \
            .values_list('id', flat=True)

    if not offer_year_id:
        scores_encodings = list(
            mdl_assess.scores_encoding.search(request.user, learning_unit_year_ids=learning_unit_year_ids))
        # Adding exam_enrollments_encoded & total_exam_enrollments
        # from each offers year for a matching learning_unit_year
        group_by_learning_unit = {}
        for score_encoding in scores_encodings:
            try:
                group_by_learning_unit[score_encoding.learning_unit_year_id].scores_not_yet_submitted \
                    += score_encoding.scores_not_yet_submitted
                group_by_learning_unit[score_encoding.learning_unit_year_id].exam_enrollments_encoded \
                    += score_encoding.exam_enrollments_encoded
                group_by_learning_unit[score_encoding.learning_unit_year_id].total_exam_enrollments \
                    += score_encoding.total_exam_enrollments
            except KeyError:
                group_by_learning_unit[score_encoding.learning_unit_year_id] = score_encoding
        scores_encodings = group_by_learning_unit.values()
    else:
        # Filter list by offer_year
        offer_year_id = int(offer_year_id)  # The offer_year_id received in session is a String, not an Int
        scores_encodings = list(mdl_assess.scores_encoding.search(request.user,
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
            learning_unit_ids_by_tutor = set(
                mdl_attr.attribution.search(tutor=tutor).values_list('learning_unit_year', flat=True))
            # learning_unit_ids_attrib = [attr.learning_unit.id for attr in attributions_by_tutor]
            scores_encodings = [score_encoding for score_encoding in scores_encodings
                                if score_encoding.learning_unit_year.id in learning_unit_ids_by_tutor]

    data = []
    all_attributions = []
    if scores_encodings:  # Empty in case there isn't any score to encode (not inside the period of scores' encoding)
        # Adding score_responsible for each learningUnit
        learning_units = [score_encoding.learning_unit_year for score_encoding in scores_encodings]
        all_attributions = list(mdl_attr.attribution.search(list_learning_unit_year=learning_units))
        coord_grouped_by_learning_unit = {attrib.learning_unit_year.id: attrib.tutor for attrib in all_attributions
                                          if attrib.score_responsible}
        for score_encoding in scores_encodings:
            progress = (score_encoding.exam_enrollments_encoded / score_encoding.total_exam_enrollments) * 100
            line = {'learning_unit_year': score_encoding.learning_unit_year,
                    'exam_enrollments_encoded': score_encoding.exam_enrollments_encoded,
                    'scores_not_yet_submitted': score_encoding.scores_not_yet_submitted,
                    'total_exam_enrollments': score_encoding.total_exam_enrollments,
                    'tutor': coord_grouped_by_learning_unit.get(score_encoding.learning_unit_year.id, None),
                    'progress': "{0:.0f}".format(progress),
                    'progress_int': progress}
            data.append(line)

    if incomplete_encodings_only:
        # Filter by completed encodings (100% complete)
        data = [line for line in data if line['exam_enrollments_encoded'] != line['total_exam_enrollments']]

    if tutor_id == NOBODY:  # LearningUnit without attribution
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

    return layout.render(request, "scores_encoding_by_learning_unit.html",
                         {'notes_list': data,
                          'offer_list': all_offers,
                          'tutor_list': all_tutors,
                          'offer_year_id': offer_year_id,
                          'tutor_id': tutor_id,
                          'academic_year': academic_yr,
                          'number_session': mdl.session_exam.find_session_exam_number(),
                          'learning_unit_year_acronym': learning_unit_year_acronym,
                          'incomplete_encodings_only': incomplete_encodings_only,
                          'last_synchronization': mdl.synchronization.find_last_synchronization_date(),
                          'active_tab': request.GET.get('active_tab', None)  # Allow keep selection
                          })


@login_required
@user_passes_test(_is_inside_scores_encodings_period, login_url=reverse_lazy('outside_scores_encodings_period'))
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
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
                exam_enrollments = mdl.exam_enrollment.sort_by_offer_acronym_last_name_first_name(exam_enrollments)
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
            'is_program_manager': is_program_manager
            }


@login_required
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def specific_criteria(request):
    data = get_data_specific_criteria(request)
    return layout.render(request, "scores_encoding_by_specific_criteria.html", data)


@login_required
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def search_by_specific_criteria(request):
    return specific_criteria(request)


@login_required
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
def specific_criteria_submission(request):
    data = get_data_specific_criteria(request)

    scores_saved = 0

    learning_unit_years_changed = []
    all_modified_exam_enrollments = []
    is_program_manager = data['is_program_manager']

    for enrollment in data['exam_enrollments']:
        learning_unit_year = enrollment.learning_unit_enrollment.learning_unit_year
        decimal_scores_authorized = learning_unit_year.decimal_scores
        try:
            updated_enrollments = update_exam_enrollments(request, [enrollment], decimal_scores_authorized,
                                                          is_program_manager)
            all_modified_exam_enrollments.extend(updated_enrollments)
            scores_saved += len(updated_enrollments)
            if len(updated_enrollments) != 0 and learning_unit_year not in learning_unit_years_changed:
                learning_unit_years_changed.append(learning_unit_year)
        except ValidationError:
            messages.add_message(request, messages.ERROR, "%s" % _('scores_must_be_between_0_and_20'))
            return specific_criteria(request)

    # ExamEnrollments by learning_unit_year (only if examEnrollment of the learningUnitYear has changed)
    grouped_by_learning_unit_years_for_mails = {}
    for enrollment in all_modified_exam_enrollments:
        learning_unit_year = enrollment.learning_unit_enrollment.learning_unit_year
        if learning_unit_year in learning_unit_years_changed:
            if learning_unit_year in grouped_by_learning_unit_years_for_mails.keys():
                grouped_by_learning_unit_years_for_mails[learning_unit_year].append(enrollment)
            else:
                grouped_by_learning_unit_years_for_mails[learning_unit_year] = [enrollment]

    for learn_unit_year, updated_exam_enrollments in grouped_by_learning_unit_years_for_mails.items():
        all_enrollments = list(mdl.exam_enrollment.find_for_score_encodings(
            session_exam_number=mdl.session_exam.find_session_exam_number(),
            learning_unit_year_id=learn_unit_year.id)
        )
        send_messages_to_notify_encoding_progress(request, all_enrollments, learn_unit_year, is_program_manager,
                                                  updated_exam_enrollments)

    messages.add_message(request, messages.SUCCESS, "%s %s" % (scores_saved, _('scores_saved')))
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


def get_json_data_scores_sheets(tutor_global_id):
    try:
        person = mdl.person.find_by_global_id(tutor_global_id)
        tutor = mdl.tutor.find_by_person(person)
        if tutor:
            exam_enrollments = list(
                mdl.exam_enrollment.find_for_score_encodings(mdl.session_exam.find_session_exam_number(),
                                                             tutor=tutor))
            data = mdl.exam_enrollment.scores_sheet_data(exam_enrollments, tutor=tutor)
            return json.dumps(data)
        else:
            return json.dumps({})
    except (PsycopOperationalError, PsycopInterfaceError, DjangoOperationalError, DjangoInterfaceError) as ep:
        trace = traceback.format_exc()
        try:
            data = json.dumps({'tutor_global_id': tutor_global_id})
            queue_exception = QueueException(queue_name=settings.QUEUES.get('QUEUES_NAME').get('PAPER_SHEET'),
                                             message=data,
                                             exception_title='[Catched and retried] - {}'.format(type(ep).__name__),
                                             exception=trace)
            queue_exception_logger.error(queue_exception.to_exception_log())
        except Exception:
            logger.error(trace)
            log_trace = traceback.format_exc()
            logger.warning('Error during queue logging :\n {}'.format(log_trace))
        connection.close()
        get_json_data_scores_sheets(tutor_global_id)
    except Exception as e:
        trace = traceback.format_exc()
        try:
            data = json.dumps({'tutor_global_id': tutor_global_id})
            queue_exception = QueueException(queue_name=settings.QUEUES.get('QUEUES_NAME').get('PAPER_SHEET'),
                                             message=data,
                                             exception_title=type(e).__name__,
                                             exception=trace)
            queue_exception_logger.error(queue_exception.to_exception_log())
        except Exception:
            logger.error(trace)
            log_trace = traceback.format_exc()
            logger.warning('Error during queue logging :\n {}'.format(log_trace))
        return None
