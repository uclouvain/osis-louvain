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
import decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from openpyxl import load_workbook

from assessments.business import score_encoding_list
from assessments.business.score_encoding_export import HEADER
from assessments.forms.score_file import ScoreFileForm
from attribution import models as mdl_attr
from base import models as mdl
from base.models.enums import exam_enrollment_justification_type as justification_types


col_academic_year = HEADER.index('academic_year')
col_session = HEADER.index('session_title')
col_learning_unit = HEADER.index('learning_unit')
col_offer = HEADER.index('program')
col_registration_id = HEADER.index('registration_number')
col_email = HEADER.index('email')
col_score = HEADER.index('numbered_score')
col_justification = HEADER.index('justification')

REGISTRATION_ID_LENGTH = 8

AUTHORIZED_JUSTIFICATION_ALIASES = {
    'T': justification_types.CHEATING,
    'A': justification_types.ABSENCE_UNJUSTIFIED
}

INFORMATIVE_JUSTIFICATION_ALIASES = {
    'S': justification_types.ABSENCE_UNJUSTIFIED,
    'M': justification_types.ABSENCE_JUSTIFIED
}


@login_required
@require_http_methods(["POST"])
@transaction.non_atomic_requests
def upload_scores_file(request, learning_unit_year_id=None):
    form = ScoreFileForm(request.POST, request.FILES)
    if form.is_valid():
        file_name = request.FILES['file']
        if file_name is not None:
            learning_unit_year = mdl.learning_unit_year.get_by_id(learning_unit_year_id)
            try:
                __save_xls_scores(request, file_name, learning_unit_year.id)
            except IndexError:
                messages.add_message(request, messages.ERROR,
                                     _("Your excel file isn't well structured. "
                                       "Please follow the structure of the excel file provided "
                                       "(button '%(button_value)s')") % {'button_value':  _('Get Excel file')})
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
        if not _is_valid_registration_id(row):
            # In case of blank line or line that is not a examEnrollment
            continue
        session = row[col_session].value
        session = int(session) if isinstance(session, str) and session.isdigit() else session
        if session and session not in sessions:
            sessions.append(session)

        try:
            academic_year = None
            if type(row[col_academic_year].value) is int:
                academic_year = int(row[col_academic_year].value)
            elif type(row[col_academic_year].value) is str:
                academic_year = int(row[col_academic_year].value[:4])
            if academic_year and academic_year not in academic_years:
                academic_years.append(academic_year)
        except (ValueError, TypeError):
            pass

        learn_unit_acronym = row[col_learning_unit].value
        if learn_unit_acronym and learn_unit_acronym not in learn_unit_acronyms:
            learn_unit_acronyms.append(learn_unit_acronym)

        offer_acronym = row[col_offer].value
        if offer_acronym and offer_acronym not in offer_acronyms:
            offer_acronyms.append(offer_acronym)

        registration_id = row[col_registration_id].value
        if registration_id and registration_id not in registration_ids:
            registration_ids.append(registration_id)

    return {'learning_unit_acronyms': learn_unit_acronyms,
            'offer_acronyms': offer_acronyms,
            'registration_ids': registration_ids,
            'sessions': sessions,
            'academic_years': academic_years}


def __save_xls_scores(request, file_name, learning_unit_year_id):
    try:
        workbook = load_workbook(file_name, read_only=True, data_only=True)
    except KeyError:
        messages.add_message(request, messages.ERROR, _("The file must be a valid 'XLSX' excel file"))
        return False
    worksheet = workbook.active
    new_scores_number = 0
    learning_unit_year = mdl.learning_unit_year.get_by_id(learning_unit_year_id)
    is_program_manager = mdl.program_manager.is_program_manager(request.user)

    data_xls = _get_all_data(worksheet)

    try:
        data_xls['session'] = _extract_session_number(data_xls)
        data_xls['academic_year'] = _extract_academic_year(data_xls)
    except Exception as e:
        messages.add_message(request, messages.ERROR, _(e.args[0]))
        return False

    academic_year_in_database = mdl.academic_year.find_academic_year_by_year(data_xls['academic_year'])
    if not academic_year_in_database:
        messages.add_message(request, messages.ERROR,
                             '%s (%s).' % (_("No data for this academic year"), data_xls['academic_year']))
        return False

    score_list = score_encoding_list.get_scores_encoding_list(
        user=request.user,
        learning_unit_year_id=learning_unit_year_id
    )

    offer_acronyms_managed_by_user = {offer_year.acronym for offer_year
                                      in score_encoding_list.find_related_offer_years(score_list)}
    learn_unit_acronyms_managed_by_user = {learning_unit_year.acronym for learning_unit_year
                                            in score_encoding_list.find_related_learning_unit_years(score_list)}
    registration_ids_managed_by_user = score_encoding_list.find_related_registration_ids(score_list)

    enrollments_grouped = _group_exam_enrollments_by_registration_id_and_learning_unit_year(score_list.enrollments)
    errors_list = {}
    # Iterates over the lines of the spreadsheet.
    for count, row in enumerate(worksheet.rows):
        if _row_can_be_ignored(row):
            continue

        row_number = count + 1
        try:
            _check_intergity_data(row,
                                  offer_acronyms_managed=offer_acronyms_managed_by_user,
                                  learn_unit_acronyms_managed=learn_unit_acronyms_managed_by_user,
                                  registration_ids_managed=registration_ids_managed_by_user,
                                  learning_unit_year=learning_unit_year)
            _check_consistency_data(row)
            updated_row = _update_row(request.user, row, enrollments_grouped, is_program_manager)
            if updated_row:
                new_scores_number+=1
        except Exception as e:
            errors_list[row_number] = e

    _show_error_messages(request, errors_list)

    if new_scores_number:
        messages.add_message(request, messages.SUCCESS, '%s %s' % (str(new_scores_number), _('Score saved')))
        if not is_program_manager:
            __warn_that_score_responsibles_must_submit_scores(request, learning_unit_year)
        return True
    else:
        messages.add_message(request, messages.ERROR, '%s' % _("No scores injected"))
        return False


def _extract_session_number(data_xls):
    if len(data_xls['sessions']) > 1:
        raise UploadValueError('more_than_one_session_error', messages.ERROR)
    elif len(data_xls['sessions']) == 0:
        raise UploadValueError('missing_column_session', messages.ERROR)
    return data_xls['sessions'][0] # Only one session


def _extract_academic_year(data_xls):
    if len(data_xls['academic_years']) > 1:
        raise UploadValueError('more_than_one_academic_year_error', messages.ERROR)
    elif len(data_xls['academic_years']) == 0:
        raise UploadValueError('no_valid_academic_year_error', messages.ERROR)

    return data_xls['academic_years'][0]  # Only one academic year


def _extract_registration_id(row):
    if _is_valid_registration_id(row):
        xls_registration_id = str(row[col_registration_id].value)
        return xls_registration_id.zfill(REGISTRATION_ID_LENGTH)
    return None


def _extract_email(row):
    return str(row[col_email].value)


def _group_exam_enrollments_by_registration_id_and_learning_unit_year(enrollments):
    exam_enrollments_by_registration_id = {}
    for enrollment in enrollments:
        key = "{}_{}".format(enrollment.learning_unit_enrollment.student.registration_id,
                             enrollment.learning_unit_enrollment.learning_unit_year.acronym)
        exam_enrollments_by_registration_id.setdefault(key, []).append(enrollment)
    return exam_enrollments_by_registration_id


def _row_can_be_ignored(row):
    return not _is_valid_registration_id(row) or _is_empty_row(row)


def _is_valid_registration_id(row):
    registration_id_value = row[col_registration_id].value
    return registration_id_value and str(registration_id_value).isdigit()


def _is_empty_row(row):
    return (row[col_score].value is None or row[col_score].value == '') and not row[col_justification].value


def _check_intergity_data(row, **kwargs):
    xls_registration_id = _extract_registration_id(row)
    xls_offer_year_acronym = row[col_offer].value
    xls_learning_unit_acronym = row[col_learning_unit].value
    registration_ids_managed = kwargs.get('registration_ids_managed')
    learn_unit_acronyms_managed = kwargs.get('learn_unit_acronyms_managed')
    offer_acronyms_managed = kwargs.get('offer_acronyms_managed')
    learning_unit_year = kwargs.get('learning_unit_year')

    if xls_registration_id not in registration_ids_managed:
        # In case the xls registration_id is not in the list, we check...
        if xls_learning_unit_acronym not in learn_unit_acronyms_managed:
            # ... if it is because the user doesn't have access to the learningUnit
            raise UploadValueError("'%s' %s" % (
                xls_learning_unit_acronym,
                _("You don't have access rights for this learning unit or it doesn't exist in our database")),
                messages.ERROR)
        elif learning_unit_year.acronym != xls_learning_unit_acronym:
            # ... if it is because the user has multiple learningUnit in his excel file
            # (the data from the DataBase are filtered by LearningUnitYear because excel file is build by learningUnit)
            raise UploadValueError(
                "%s" % _("You encoded scores for more than 1 learning unit in your excel file (column 'Learning unit')."
                         "Please make one excel file by learning unit."), messages.ERROR)
        elif xls_offer_year_acronym not in offer_acronyms_managed:
            # ... if it is because the user haven't access rights to the offerYear
            raise UploadValueError(
                "'%s' %s" % (xls_offer_year_acronym,
                             _("You don't have access rights for this offer or it doesn't exist in our database")),
                messages.ERROR)
        else:
            # ... if it's beacause the registration id doesn't exist
            raise UploadValueError("%s" % _("Student not registered for exam"), messages.ERROR)


def _check_consistency_data(row):
    xls_registration_id = _extract_registration_id(row)
    xls_email = _extract_email(row)
    if not _registration_id_matches_email(xls_registration_id, xls_email):
        raise UploadValueError("%s" % _("Registration ID does not match email"), messages.ERROR)


def _registration_id_matches_email(registration_id, email):
    student_by_registration_id = mdl.student.find_by_registration_id(registration_id)
    return str(student_by_registration_id.person.email).strip() == email.strip()


def _update_row(user, row, enrollments_managed_grouped, is_program_manager):
    xls_registration_id = _extract_registration_id(row)
    xls_learning_unit_acronym = row[col_learning_unit].value
    xls_score = _clean_value(row[col_score].value)
    xls_justification = _clean_value(row[col_justification].value)

    key = "{}_{}".format(xls_registration_id, xls_learning_unit_acronym)
    enrollments = enrollments_managed_grouped.get(key, [])

    if not enrollments:
        raise ValueError("%s!" %
                         _("The enrollment to the activity %(xls_learning_unit_acronym)s doesn't exist")
                         % xls_learning_unit_acronym)

    enrollment = enrollments[0]

    if score_encoding_list.is_deadline_reached(enrollment, is_program_manager):
        raise UploadValueError("%s" % _("Deadline reached"), messages.ERROR)

    if not is_program_manager and enrollment.is_final:
        raise UploadValueError("%s" % _("Score already submitted"), messages.WARNING)

    if (xls_score or xls_score == 0) and xls_justification:
        raise UploadValueError("%s" % _("You can't encode a 'score' and a 'justification' together"), messages.ERROR)

    if xls_justification and _is_informative_justification(enrollment, xls_justification, is_program_manager):
       return False

    enrollment.score_encoded = xls_score
    enrollment.justification_encoded = None
    if xls_justification:
        enrollment.justification_encoded = _get_justification_from_aliases(enrollment, xls_justification)
    return score_encoding_list.update_enrollment(
        enrollment=enrollment,
        user=user
    )


def _clean_value(value):
    return value.strip() if isinstance(value, str) else value


def _is_informative_justification(enrollment, xls_justification, is_program_manager):
    justification = enrollment.justification_final if is_program_manager else enrollment.justification_draft
    justification_informative = INFORMATIVE_JUSTIFICATION_ALIASES.get(xls_justification)

    return justification and justification_informative and justification == justification_informative


def __warn_that_score_responsibles_must_submit_scores(request, learning_unit_year):
    tutor = mdl.tutor.find_by_user(request.user)
    if tutor and not mdl_attr.attribution.is_score_responsible(request.user, learning_unit_year):
        messages.add_message(request, messages.SUCCESS,
                             '%s' % _("The scores responsible must still submit the scores"))


def _get_justification_from_aliases(enrollment, justification_encoded):
    justification_encoded = justification_encoded.upper() if isinstance(justification_encoded, str) \
                            else justification_encoded
    justification = AUTHORIZED_JUSTIFICATION_ALIASES.get(justification_encoded)
    if justification:
        _check_is_user_try_change_justified_to_unjustified_absence(enrollment, justification)
        return justification
    else:
        raise UploadValueError('%s' % _("Invalid justification value"), messages.ERROR)


def _check_is_user_try_change_justified_to_unjustified_absence(enrollment, justification):
    if justification == justification_types.ABSENCE_UNJUSTIFIED and \
       enrollment.justification_final == justification_types.ABSENCE_JUSTIFIED:
            raise UploadValueError(
                '%s' % _("Absence justified cannot be remplaced by absence unjustified"), messages.ERROR)


def _show_error_messages(request, errors_list):
    errors_list_grouped = _errors_list_group_by_message(errors_list)
    for message, error in errors_list_grouped.items():
        rows_number = sorted(error.get('rows_number', []))
        str_rows_number_formated = ', '.join([str(nb) for nb in rows_number])
        messages.add_message(request, error.get('level'), "%s : %s %s" % (message, _('Line'),
                                                                          str_rows_number_formated))


def _errors_list_group_by_message(errors_list):
    errors_grouped_by_message = {}
    for row_number, error in errors_list.items():
        message = _extract_error_message(error)
        level = _extract_level_error(error)
        errors_grouped_by_message.setdefault(message, {'level': level, 'rows_number': []})
        errors_grouped_by_message[message]['rows_number'].append(row_number)

    return errors_grouped_by_message


def _extract_error_message(error):
    if isinstance(error, UploadValueError):
        return _(error.value)
    elif isinstance(error, ValidationError):
        return _(error.messages[0])
    elif isinstance(error, decimal.InvalidOperation):
        return _("Scores must be between 0 and 20")
    return _(error.args[0])


def _extract_level_error(error):
    if isinstance(error, UploadValueError):
        return error.message
    return messages.ERROR


class UploadValueError(ValueError):
    def __init__(self, value, message):
        self.value = value
        self.message = message
