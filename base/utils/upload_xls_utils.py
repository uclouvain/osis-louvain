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
from django.utils.translation import ungettext
from openpyxl import load_workbook
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from base.forms import ScoreFileForm
from base import models as mdl


@login_required
def upload_scores_file(request, learning_unit_year_id=None):
    if request.method == 'POST':
        form = ScoreFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_name = request.FILES['file']
            if file_name is not None:
                if ".xls" not in str(file_name):
                    messages.add_message(request, messages.INFO, _('file_must_be_xls'))
                else:
                    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
                    is_program_manager = mdl.program_manager.is_program_manager(request.user)
                    __save_xls_scores(request, file_name, is_program_manager, request.user,
                                      learning_unit_year.learning_unit.id)

        return HttpResponseRedirect(reverse('online_encoding', args=[learning_unit_year_id, ]))


def __save_xls_scores(request, file_name, is_program_manager, user, learning_unit_id):
    workbook = load_workbook(file_name, read_only=True)
    worksheet = workbook.active
    new_scores_number = 0
    new_scores = False
    session_exam = None

    col_academic_year = 0
    col_session = 1
    col_learning_unit = 2
    col_offer = 3
    col_registration_id = 4
    col_score = 7
    col_justification = 8

    # Iterates over the lines of the spreadsheet.
    for count, row in enumerate(worksheet.rows):
        new_score = False
        if row[col_registration_id].value is None \
                or len(row[col_registration_id].value) == 0 \
                or not _is_registration_id(row[col_registration_id].value):
            continue

        student = mdl.student.find_by(registration_id=row[col_registration_id].value)
        info_line = "%s %d (NOMA %s):" % (_('Line'), count + 1, row[col_registration_id].value)
        if not student:
            messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('student_not_exist') % (str(row[col_registration_id].value))))
        else:
            academic_year = mdl.academic_year.find_academic_year_by_year(int(row[col_academic_year].value[:4]))
            if not academic_year:
                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('academic_year_not_exist') % row[col_academic_year].value))
            else:
                offer_year = mdl.offer_year.find_by_academicyear_acronym(academic_year, row[col_offer].value)
                if not offer_year:
                    messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('offer_year_not_exist') % (str(row[col_offer].value), academic_year.year)))
                else:
                    offer_enrollment = mdl.offer_enrollment.find_by_student_offer(student, offer_year)
                    if not offer_enrollment:
                        messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('offer_enrollment_not_exist')))
                    else:
                        learning_unit_year_lists = mdl.learning_unit_year.search(academic_year,
                                                                                 row[col_learning_unit].value)
                        learning_unit_year = None
                        if len(learning_unit_year_lists) == 1:
                            learning_unit_year = learning_unit_year_lists[0]
                        if not learning_unit_year:
                            messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('activity_not_exit') % (str(row[col_learning_unit].value))))
                        else:
                            learning_unit_enrollment = mdl.learning_unit_enrollment.find_by_learningunit_enrollment(learning_unit_year, offer_enrollment)
                            if not learning_unit_enrollment:
                                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('enrollment_activity_not_exist') % (str(row[col_learning_unit].value))))
                            else:
                                session_number = int(row[col_session].value)
                                exam_enrollment = mdl.exam_enrollment.find_by_enrollment_session(learning_unit_enrollment, session_number)
                                if row[col_learning_unit].value != exam_enrollment.learning_unit_enrollment.learning_unit_year.acronym:
                                    learning_unit = mdl.learning_unit.find_by_id(learning_unit_id)
                                    messages.add_message(request, messages.ERROR, "%s %s for %s!" % (info_line, _('enrollment_exam_not_exists'), learning_unit.acronym))
                                else:
                                    if session_exam is None:
                                        session_exam = exam_enrollment.session_exam
                                    if is_program_manager:
                                        notes_modifiable = True
                                    else:
                                        if exam_enrollment.score_final is None and not exam_enrollment.justification_final:
                                            notes_modifiable = True
                                        else:
                                            notes_modifiable = False
                                            messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('score_already_submitted')))
                                    score = None
                                    if notes_modifiable:
                                        if row[col_score].value is not None:
                                            try:
                                                score = float(str(row[col_score].value).strip().replace(',', '.'))
                                            except ValueError:
                                                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('score_invalid')))
                                        else:
                                            score = None

                                        score_valid = True

                                        if score is not None:
                                            if score < 0 or score > 20:
                                                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('scores_gt_0_lt_20')))
                                                score_valid = False
                                            elif not learning_unit_year.decimal_scores and round(score) != score:
                                                messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('score_decimal_not_allowed')))
                                                score_valid = False
                                        else:
                                            score_valid = False

                                        justification_xls = None
                                        justification_value = row[col_justification].value
                                        justification_valid = False
                                        if justification_value:
                                            justification_value = justification_value.strip()
                                            if justification_value in ['A', 'T', '?']:
                                                switcher = {'A': "ABSENCE_UNJUSTIFIED",
                                                            'T': "CHEATING",
                                                            '?': "SCORE_MISSING"}
                                                justification_xls = switcher.get(justification_value, None)
                                                justification_valid = True

                                        if score and justification_xls:
                                            score_valid = False
                                            justification_valid = False
                                            messages.add_message(request, messages.ERROR, "%s %s!" % (info_line, _('constraint_score_other_score')))

                                        if score_valid or justification_valid:
                                            if is_program_manager:
                                                if exam_enrollment.score_final != score:
                                                    new_scores_number += 1
                                                    new_scores = True
                                                    new_score = True

                                                if (justification_valid and justification_xls and exam_enrollment.justification_final != justification_xls) \
                                                        or (not is_program_manager and exam_enrollment.justification_draft != justification_xls):
                                                    new_scores_number += 1
                                                    new_scores = True
                                                    new_score = True
                                            else:
                                                if score != exam_enrollment.score_draft:
                                                    new_scores_number += 1
                                                    new_scores = True
                                                    new_score = True

                                                if justification_valid and justification_xls and exam_enrollment.justification_draft != justification_xls:
                                                    new_scores_number += 1
                                                    new_scores = True
                                                    new_score = True

                                        if new_score:
                                            if is_program_manager:
                                                exam_enrollment.score_final = score
                                                exam_enrollment.justification_final = justification_xls
                                            else:
                                                exam_enrollment.score_draft = score
                                                exam_enrollment.justification_draft = justification_xls

                                            exam_enrollment.save()

                                            if is_program_manager:
                                                mdl.exam_enrollment.create_exam_enrollment_historic(request.user,
                                                                                                    exam_enrollment,
                                                                                                    score,
                                                                                                    justification_xls)

    if session_exam is not None:
        all_encoded = True
        enrollments = mdl.exam_enrollment.find_exam_enrollments_by_session(session_exam)
        for enrollment in enrollments:
            if enrollment.score_final is None and not enrollment.justification_final:
                all_encoded = False

    if new_scores:
        if new_scores_number > 0:
            count = new_scores_number
            text = ungettext('%(count)d %(name)s.',
                             '%(count)d %(plural_name)s.',
                             count) % {'count': new_scores_number,
                                       'name': _('score_saved'),
                                       'plural_name':  _('scores_saved')}

            messages.add_message(request, messages.INFO, '%s' % text)
            if not is_program_manager:
                tutor = mdl.tutor.find_by_user(user)
                if tutor and learning_unit_id:
                    coordinator = mdl.attribution.search(tutor=tutor,
                                                         learning_unit_id=learning_unit_id,
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