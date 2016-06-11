##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from openpyxl import load_workbook
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from base.forms import ScoreFileForm
from base import models as mdl


col_academic_year = 0
col_session = 1
col_learning_unit = 2
col_offer = 3
col_registration_id = 4
col_score = 7
col_justification = 8

REGISTRATION_ID_SIZE = 8 # Size of all registration ids (convention)


@login_required
def upload_scores_file(request, learning_unit_year_id=None):
    if request.method == 'POST':
        form = ScoreFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_name = request.FILES['file']
            if file_name is not None:
                learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
                is_program_manager = mdl.program_manager.is_program_manager(request.user)
                __save_xls_scores(request, file_name, is_program_manager, request.user,
                                  learning_unit_year.id)
        else:
            for error_msg in [error_msg for error_msgs in form.errors.values() for error_msg in error_msgs]:
                messages.add_message(request, messages.ERROR, "{}".format(error_msg))
        return HttpResponseRedirect(reverse('online_encoding', args=[learning_unit_year_id, ]))


def _get_all_data(worksheet):
    """
    :param worksheet: The excel worksheet (containing examEnrollments/scores)
    :return: All learn_unit_acronyms, offer_acronyms, registration_ids, session and academic_years
             in all lines of the worksheet.
    """
    learn_unit_acronyms = []
    offer_acronyms = []
    registration_ids = []
    sessions = []
    academic_years = []
    for count, row in enumerate(worksheet.rows):
        if row[col_registration_id].value is None \
                or len(str(row[col_registration_id].value)) == 0 \
                or not _is_registration_id(row[col_registration_id].value):
            # In case of blank line or line that is not a examEnrollment
            continue
        session = row[col_session].value
        if session not in sessions:
            sessions.append(session)

        try:
            academic_year = int(row[col_academic_year].value[:4])
            if academic_year not in academic_years:
                academic_years.append(academic_year)
        except ValueError:
            pass

        learn_unit_acronym = row[col_learning_unit].value
        if learn_unit_acronym not in learn_unit_acronyms:
            learn_unit_acronyms.append(learn_unit_acronym)

        offer_acronym = row[col_offer].value
        if offer_acronym not in offer_acronyms:
            offer_acronyms.append(offer_acronym)

        registration_id = row[col_registration_id].value
        if registration_id not in registration_ids:
            registration_ids.append(registration_id)

    return {'learning_unit_acronyms': learn_unit_acronyms,
            'offer_acronyms': offer_acronyms,
            'registration_ids': registration_ids,
            'sessions': sessions,
            'academic_years': academic_years}


def __save_xls_scores(request, file_name, is_program_manager, user, learning_unit_year_id):
    try:
        workbook = load_workbook(file_name, read_only=True)
    except KeyError:
        messages.add_message(request, messages.ERROR, _('file_must_be_xlsx'))
        return False
    worksheet = workbook.active
    new_scores_number = 0
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)

    data_xls = _get_all_data(worksheet)
    if len(data_xls['sessions']) > 1:
        messages.add_message(request, messages.ERROR, '%s' % _('more_than_one_session_error'))
        return False
    else:
        data_xls['session'] = data_xls['sessions'][0]  # Only one session

    if len(data_xls['academic_years']) > 1:
        messages.add_message(request, messages.ERROR, '%s' % _('more_than_one_academic_year_error'))
        return False
    else:
        data_xls['academic_year'] = data_xls['academic_years'][0]  # Only one session

    academic_year_in_database = mdl.academic_year.find_academic_year_by_year(data_xls['academic_year'])
    if is_program_manager:
        offer_years_managed = list(mdl.offer_year.find_by_user(user, academic_yr=academic_year_in_database))
        exam_enrollments_managed_by_user = list(mdl.exam_enrollment.find_for_score_encodings(data_xls['session'],
                                                                                             offers_year=offer_years_managed,
                                                                                             learning_unit_year_id=learning_unit_year_id))
        # Set of all LearningUnit.acronym managed by the user
        learn_unit_acronyms_managed_by_user = {exam_enroll.learning_unit_enrollment.learning_unit_year.acronym
                                               for exam_enroll in exam_enrollments_managed_by_user}
        # Set of all OfferYear.acronym managed by the user
        offer_acronyms_managed_by_user = {offer_year.acronym for offer_year in offer_years_managed}
    else:
        tutor = mdl.tutor.find_by_user(request.user)
        exam_enrollments_managed_by_user = list(mdl.exam_enrollment.find_for_score_encodings(data_xls['session'],
                                                                                             tutor=tutor,
                                                                                             learning_unit_year_id=learning_unit_year_id))
        learning_unit_years = list(mdl.learning_unit_year.find_by_tutor(tutor.id))
        # Set of all LearningUnit.acronym managed by the user
        learn_unit_acronyms_managed_by_user = {learning_unit_year.acronym for learning_unit_year in learning_unit_years}
        # Set of all OfferYear.acronym managed by the user
        offer_acronyms_managed_by_user = {exam_enroll.learning_unit_enrollment.offer_enrollment.offer_year.acronym
                                          for exam_enroll in exam_enrollments_managed_by_user}

    # Set of all Student.registration_id managed by the user
    registration_ids_managed_by_user = {exam_enroll.learning_unit_enrollment.student.registration_id
                                           for exam_enroll in exam_enrollments_managed_by_user}
    # Dictionary where key=Student.registration_id and value=ExamEnrollment (object from queryset)
    exam_enrollments_by_registration_id = {}
    for exam_enroll in exam_enrollments_managed_by_user:
        registration_id = exam_enroll.learning_unit_enrollment.student.registration_id
        if registration_id in exam_enrollments_by_registration_id.keys():
            exam_enrollments_by_registration_id[registration_id].append(exam_enroll)
        else:
            exam_enrollments_by_registration_id[registration_id] = [exam_enroll]

    # Iterates over the lines of the spreadsheet.
    for count, row in enumerate(worksheet.rows):
        if row[col_registration_id].value is None \
                or len(str(row[col_registration_id].value)) == 0 \
                or not _is_registration_id(row[col_registration_id].value):
            continue
        elif (row[col_score].value is None or row[col_score].value == '') and not row[col_justification].value:
            # If there's no score/justification encoded for this line, not necessary to make all checks below
            continue
        xls_registration_id = str(row[col_registration_id].value)
        xls_registration_id = xls_registration_id.zfill(REGISTRATION_ID_SIZE)
        xls_offer_year_acronym = row[col_offer].value
        xls_learning_unit_acronym = row[col_learning_unit].value
        info_line = "%s %d (NOMA %s):" % (_('Line'), count + 1, xls_registration_id)
        if xls_registration_id not in registration_ids_managed_by_user:
            # In case the xls registration_id is not in the list, we check...
            if xls_learning_unit_acronym not in learn_unit_acronyms_managed_by_user:
                # ... if it is because the user doesn't have access to the learningUnit
                messages.add_message(request, messages.ERROR, "%s '%s' %s!" % (info_line, xls_learning_unit_acronym, _('learning_unit_not_access_or_not_exist')))
            elif learning_unit_year.acronym != xls_learning_unit_acronym:
                # ... if it is because the user has multiple learningUnit in his excel file
                # (the data from the DataBase are filtered by LearningUnitYear because excel file is build by learningUnit)
                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('more_than_one_learning_unit_error')))
            elif xls_offer_year_acronym not in offer_acronyms_managed_by_user:
                # ... if it is because the user haven't access rights to the offerYear
                messages.add_message(request, messages.ERROR, "%s '%s' %s!" % (info_line, xls_offer_year_acronym, _('offer_year_not_access_or_not_exist')))
            else:
                # ... if it's beacause the registration id doesn't exist
                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('registration_id_not_access_or_not_exist')))
        else:
            exam_enrollments = exam_enrollments_by_registration_id.get(xls_registration_id, [])
            exam_enrollment = None
            count_exam_enrol_for_this_learn_unit = 0 # A student could have 2 examEnrollments for a same learningUnit in 2 different offers
            # Find ExamEnrollment by learningUnit.acronym
            for exam_enroll in exam_enrollments:
                if exam_enroll.learning_unit_enrollment.learning_unit_year.acronym == xls_learning_unit_acronym:
                    exam_enrollment = exam_enroll
                    count_exam_enrol_for_this_learn_unit +=1
            if not exam_enrollment:
                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('enrollment_activity_not_exist') % (xls_learning_unit_acronym)))
            elif not is_program_manager and (exam_enrollment.score_final is not None or exam_enrollment.justification_final):
                # In case the user is not a program manager, we check if the scores are already submitted
                # If this examEnrollment is already encoded in DataBase, nothing to do (ingnoring the line)
                messages.add_message(request, messages.WARNING, "%s %s!" % (info_line, _('score_already_submitted')))
                continue
            else:
                academic_year = int(row[col_academic_year].value[:4])
                if academic_year != academic_year_in_database.year:
                    messages.add_message(request, messages.ERROR, "%s '%d' %s!" % (info_line, academic_year, _('academic_year_not_exist')))
                else:
                    if xls_offer_year_acronym not in offer_acronyms_managed_by_user:
                        messages.add_message(request, messages.ERROR, "%s '%s' %s!" % (info_line, xls_offer_year_acronym, _('offer_year_not_access_or_not_exist')))
                    elif xls_offer_year_acronym != exam_enrollment.learning_unit_enrollment.offer_enrollment.offer_year.acronym:
                        if count_exam_enrol_for_this_learn_unit > 1:
                            # A student could have 2 exam enrollments for a same learningUnit in 2 different offers
                            messages.add_message(request, messages.ERROR, "%s %s" % (info_line, _('more_than_one_exam_enrol_for_one_learn_unit')))
                        else:
                            messages.add_message(request, messages.ERROR, "%s '%s' %s!" % (info_line, xls_offer_year_acronym, _('offer_enrollment_not_exist')))
                    else:
                        if xls_learning_unit_acronym not in learn_unit_acronyms_managed_by_user:
                            messages.add_message(request, messages.ERROR, "%s '%s' %s!" % (info_line, xls_learning_unit_acronym, _('learning_unit_not_access_or_not_exist')))
                        else:
                            if xls_learning_unit_acronym != exam_enrollment.learning_unit_enrollment.learning_unit_year.acronym:
                                messages.add_message(request, messages.ERROR, "%s %s for %s!" % (info_line, _('enrollment_exam_not_exists'), xls_learning_unit_acronym))
                            else:
                                score = row[col_score].value
                                score = score.replace(" ", "") if type(score) == str else score
                                score = None if score == '' else score  # The score could be an Integer or String...
                                if score is not None:
                                    try:
                                        score = float(str(row[col_score].value).strip().replace(',', '.'))
                                    except ValueError:
                                        messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('score_invalid')))
                                        continue
                                    if score < 0 or score > 20:
                                        messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('scores_gt_0_lt_20')))
                                        continue
                                    elif not exam_enrollment.learning_unit_enrollment.learning_unit_year.decimal_scores and round(score) != score:
                                        messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('score_decimal_not_allowed')))
                                        continue

                                justification = row[col_justification].value
                                justification = justification.replace(" ", "") if type(justification) == str else justification
                                if justification:
                                    justification = str(justification).strip().upper()
                                    if justification in ['A', 'T', '?']:
                                        switcher = {'A': "ABSENCE_UNJUSTIFIED",
                                                    'T': "CHEATING",
                                                    '?': "SCORE_MISSING"}
                                        justification = switcher.get(justification, None)
                                    else:
                                        messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('justification_invalid')))
                                        continue

                                if score is not None and justification:
                                    messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('constraint_score_other_score')))

                                elif score == 0 or score or justification:
                                    if is_program_manager:
                                        if exam_enrollment.score_final != score:
                                            new_scores_number += 1
                                            exam_enrollment.score_final = score

                                        if (justification and exam_enrollment.justification_final != justification) \
                                                or (not is_program_manager and exam_enrollment.justification_draft != justification):
                                            new_scores_number += 1
                                            exam_enrollment.justification_final = justification
                                        mdl.exam_enrollment.create_exam_enrollment_historic(request.user,
                                                                                            exam_enrollment,
                                                                                            score,
                                                                                            justification)
                                    else:
                                        if score != exam_enrollment.score_draft:
                                            new_scores_number += 1
                                            exam_enrollment.score_draft = score

                                        if justification and exam_enrollment.justification_draft != justification:
                                            new_scores_number += 1
                                            exam_enrollment.justification_draft = justification
                                    exam_enrollment.save()

    if new_scores_number > 0:
        messages.add_message(request, messages.INFO, '%s %s' % (str(new_scores_number), _('score_saved')))
        if not is_program_manager:
            tutor = mdl.tutor.find_by_user(user)
            if tutor and learning_unit_year.learning_unit_id:
                coordinator = mdl.attribution.search(tutor=tutor,
                                                     learning_unit_id=learning_unit_year.learning_unit_id,
                                                     function='COORDINATOR')
                if not coordinator:
                    messages.add_message(request, messages.INFO, '%s' % _('the_coordinator_must_still_submit_scores'))
        return True
    else:
        messages.add_message(request, messages.ERROR, '%s' % _('no_score_injected'))
        return False


def _is_registration_id(registration_id):
    try:
        int(registration_id)
        return True
    except ValueError:
        return False
