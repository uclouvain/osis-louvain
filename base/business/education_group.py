##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Dict

from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.business.xls import get_name_or_username, convert_boolean
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums import mandate_type as mandate_types
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.mandate import Mandate
from base.models.offer_year_calendar import OfferYearCalendar
from education_group.models.group_year import GroupYear
from osis_common.document import xls_build
from program_management.models.education_group_version import EducationGroupVersion

# List of key that a user can modify
DATE_FORMAT = '%d-%m-%Y'
DATE_TIME_FORMAT = '%d-%m-%Y %H:%M'
DESC = "desc"
WORKSHEET_TITLE = _('Education_groups')
XLS_FILENAME = _('Education_groups')
XLS_DESCRIPTION = _("List education groups")
EDUCATION_GROUP_TITLES = [str(_('Ac yr.')), str(pgettext_lazy('abbreviation', 'Acronym/Short title')),
                          str(_('Title')), str(_('Type')), str(_('Entity')), str(_('Code'))]
ORDER_COL = 'order_col'
ORDER_DIRECTION = 'order_direction'
#

WORKSHEET_TITLE_ADMINISTRATIVE = _('Trainings')
XLS_FILENAME_ADMINISTRATIVE = _('training_administrative_data')
XLS_DESCRIPTION_ADMINISTRATIVE = _("List of trainings with administrative data")

# Column for xls with administrative data
MANAGEMENT_ENTITY_COL = _('Management entity')
TRANING_COL = _('Training')
TYPE_COL = _('Type')
ACADEMIC_YEAR_COL = _('Validity')
START_COURSE_REGISTRATION_COL = _('Begining of course registration')
END_COURSE_REGISTRATION_COL = _('Ending of course registration')
START_EXAM_REGISTRATION_COL = _('Begining of exam registration')
END_EXAM_REGISTRATION_COL = _('Ending of exam registration')
MARKS_PRESENTATION_COL = _('Marks presentation')
DISSERTATION_PRESENTATION_COL = _('Dissertation presentation')
DELIBERATION_COL = _('Deliberation')
SCORES_DIFFUSION_COL = _('Scores diffusion')
WEIGHTING_COL = _('Weighting')
DEFAULT_LEARNING_UNIT_ENROLLMENT_COL = _('Default learning unit enrollment')
CHAIR_OF_THE_EXAM_BOARD_COL = _('Chair of the exam board')
EXAM_BOARD_SECRETARY_COL = _('Exam board secretary')
EXAM_BOARD_SIGNATORY_COL = _('Exam board signatory')
SIGNATORY_QUALIFICATION_COL = _('Signatory qualification')

SESSIONS_COLUMNS = 'sessions_columns'
SESSIONS_NUMBER = 3
SESSION_HEADERS = [
    START_EXAM_REGISTRATION_COL,
    END_EXAM_REGISTRATION_COL,
    MARKS_PRESENTATION_COL,
    DISSERTATION_PRESENTATION_COL,
    DELIBERATION_COL,
    SCORES_DIFFUSION_COL
]
EDUCATION_GROUP_TITLES_ADMINISTRATIVE = [
    MANAGEMENT_ENTITY_COL,
    TRANING_COL,
    TYPE_COL,
    ACADEMIC_YEAR_COL,
    START_COURSE_REGISTRATION_COL,
    END_COURSE_REGISTRATION_COL,
    SESSIONS_COLUMNS,   # this columns will be duplicate by SESSIONS_NUMBER [content: SESSION_HEADERS]
    WEIGHTING_COL,
    DEFAULT_LEARNING_UNIT_ENROLLMENT_COL,
    CHAIR_OF_THE_EXAM_BOARD_COL,
    EXAM_BOARD_SECRETARY_COL,
    EXAM_BOARD_SIGNATORY_COL,
    SIGNATORY_QUALIFICATION_COL,
]


def prepare_xls_content(found_education_groups: List[GroupYear]) -> List:
    return [extract_xls_data_from_education_group(eg) for eg in found_education_groups]


def extract_xls_data_from_education_group(group_year: GroupYear) -> List:
    """ At this stage, the group_year has been annotated with property complete_title_fr / full_title_fr"""
    return [
        group_year.academic_year.name,
        group_year.complete_title_fr,
        group_year.full_title_fr,
        group_year.education_group_type,
        group_year.management_entity_version.acronym if group_year.management_entity_version else '',
        group_year.partial_acronym
    ]


def ordering_data(object_list, order_data):
    order_col = order_data.get(ORDER_COL)
    order_direction = order_data.get(ORDER_DIRECTION)
    reverse_direction = order_direction == DESC

    return sorted(list(object_list), key=lambda t: _get_field_value(t, order_col), reverse=reverse_direction)


def _get_field_value(instance, field):
    field_path = field.split('.')
    attr = instance
    for elem in field_path:
        try:
            attr = getattr(attr, elem) or ''
        except AttributeError:
            return None
    return attr


def create_xls_administrative_data(user, education_group_years_qs, filters, order_data, language: str):
    # Make select_related/prefetch_related in order to have low DB HIT
    education_group_years = education_group_years_qs.filter(
        education_group_type__category=education_group_categories.TRAINING
    ).select_related(
        'educationgroupversion__offer__education_group_type',
        'educationgroupversion__offer__academic_year',
    ).prefetch_related(
        Prefetch(
            'educationgroupversion__offer__education_group__mandate_set',
            queryset=Mandate.objects.prefetch_related('mandatary_set')
        ),
        Prefetch(
            'educationgroupversion__offer__offeryearcalendar_set',
            queryset=OfferYearCalendar.objects.select_related('academic_calendar__sessionexamcalendar')
        )
    )
    found_education_groups = ordering_data(education_group_years, order_data)
    # FIXME: should be improved with ddd usage

    working_sheets_data = prepare_xls_content_administrative(
        [gy.educationgroupversion for gy in found_education_groups],
        language
    )
    header_titles = _get_translated_header_titles()
    parameters = {
        xls_build.DESCRIPTION: XLS_DESCRIPTION_ADMINISTRATIVE,
        xls_build.USER: get_name_or_username(user),
        xls_build.FILENAME: XLS_FILENAME_ADMINISTRATIVE,
        xls_build.HEADER_TITLES: header_titles,
        xls_build.WS_TITLE: WORKSHEET_TITLE_ADMINISTRATIVE
    }
    return xls_build.generate_xls(xls_build.prepare_xls_parameters_list(working_sheets_data, parameters), filters)


def _get_translated_header_titles() -> List[str]:
    translated_headers = []
    for title in EDUCATION_GROUP_TITLES_ADMINISTRATIVE:
        if title != SESSIONS_COLUMNS:
            translated_headers.append(str(_(title)))
        else:
            translated_headers.extend(_get_translated_header_session_columns())
    return translated_headers


def _get_translated_header_session_columns():
    translated_session_headers = []
    for title in SESSION_HEADERS:
        translated_session_headers.append(str(_(title)))

    # Duplicate translation by nb_session + append nb_session to title
    all_headers_sessions = []
    for session_number in range(1, SESSIONS_NUMBER + 1):
        all_headers_sessions += ["{} {} ".format(translated_title, session_number) for translated_title in
                                 translated_session_headers]
    return all_headers_sessions


def prepare_xls_content_administrative(education_group_versions: List[EducationGroupVersion], language: str):
    xls_data = []
    for education_group_version in education_group_versions:
        education_group_year = education_group_version.offer
        main_data = _extract_main_data(education_group_version, language)
        administrative_data = _extract_administrative_data(education_group_year)
        mandatary_data = _extract_mandatary_data(education_group_year)

        # Put all dict together and ordered it by EDUCATION_GROUP_TITLES_ADMINISTRATIVE
        row = _convert_data_to_xls_row(
            education_group_year_data={**main_data, **administrative_data, **mandatary_data},
            header_list=EDUCATION_GROUP_TITLES_ADMINISTRATIVE
        )
        xls_data.append(row)
    return xls_data


def _extract_main_data(a_version: EducationGroupVersion, language) -> Dict:
    an_education_group_year = a_version.offer
    return {
        MANAGEMENT_ENTITY_COL:
            an_education_group_year.management_entity_version.acronym
            if an_education_group_year.management_entity_version else '',
        TRANING_COL: "{}{}".format(
            an_education_group_year.acronym,
            a_version.version_label()
        ),
        TYPE_COL: "{}{}".format(
            an_education_group_year.education_group_type,
            _get_title(a_version, language)
        ),
        ACADEMIC_YEAR_COL: an_education_group_year.academic_year.name,
        WEIGHTING_COL: convert_boolean(an_education_group_year.weighting),
        DEFAULT_LEARNING_UNIT_ENROLLMENT_COL: convert_boolean(an_education_group_year.default_learning_unit_enrollment)
    }


def _extract_administrative_data(an_education_group_year: EducationGroupYear) -> Dict:
    course_enrollment_calendar = _get_offer_year_calendar_from_prefetched_data(
        an_education_group_year,
        AcademicCalendarTypes.COURSE_ENROLLMENT.name
    )
    administrative_data = {
        START_COURSE_REGISTRATION_COL: _format_date(course_enrollment_calendar, 'start_date', DATE_FORMAT),
        END_COURSE_REGISTRATION_COL: _format_date(course_enrollment_calendar, 'end_date', DATE_FORMAT),
        SESSIONS_COLUMNS: [
            _extract_session_data(an_education_group_year, session_number) for
            session_number in range(1, SESSIONS_NUMBER + 1)
        ]
    }
    return administrative_data


def _extract_session_data(education_group_year: EducationGroupYear, session_number: int) -> Dict:
    session_academic_cal_type = [
        AcademicCalendarTypes.EXAM_ENROLLMENTS.name,
        AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
        AcademicCalendarTypes.DISSERTATION_SUBMISSION.name,
        AcademicCalendarTypes.DELIBERATION.name,
        AcademicCalendarTypes.SCORES_EXAM_DIFFUSION.name
    ]
    offer_year_cals = {}
    for academic_cal_type in session_academic_cal_type:
        offer_year_cals[academic_cal_type] = _get_offer_year_calendar_from_prefetched_data(
            education_group_year,
            academic_cal_type,
            session_number=session_number
        )

    return {
        START_EXAM_REGISTRATION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.EXAM_ENROLLMENTS.name], 'start_date', DATE_FORMAT
        ),
        END_EXAM_REGISTRATION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.EXAM_ENROLLMENTS.name], 'end_date', DATE_FORMAT
        ),
        MARKS_PRESENTATION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name], 'start_date', DATE_FORMAT
        ),
        DISSERTATION_PRESENTATION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.DISSERTATION_SUBMISSION.name], 'start_date', DATE_FORMAT
        ),
        DELIBERATION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.DELIBERATION.name], 'start_date', DATE_TIME_FORMAT
        ),
        SCORES_DIFFUSION_COL: _format_date(
            offer_year_cals[AcademicCalendarTypes.SCORES_EXAM_DIFFUSION.name], 'start_date', DATE_TIME_FORMAT
        ),
    }


def _extract_mandatary_data(education_group_year: EducationGroupYear) -> Dict:
    representatives = {mandate_types.PRESIDENT: [], mandate_types.SECRETARY: [], mandate_types.SIGNATORY: []}

    for mandate in education_group_year.education_group.mandate_set.all():
        representatives = _get_representatives(education_group_year, mandate, representatives)

    return {
        CHAIR_OF_THE_EXAM_BOARD_COL: names(representatives[mandate_types.PRESIDENT]),
        EXAM_BOARD_SECRETARY_COL: names(representatives[mandate_types.SECRETARY]),
        EXAM_BOARD_SIGNATORY_COL: names(representatives[mandate_types.SIGNATORY]),
        SIGNATORY_QUALIFICATION_COL: qualification(representatives[mandate_types.SIGNATORY]),
    }


def _get_representatives(education_group_year, mandate, representatives_param):
    representatives = representatives_param
    for mandataries in mandate.mandatary_set.all():
        if _is_valid_mandate(mandataries, education_group_year):
            if mandataries.mandate.function == mandate_types.PRESIDENT:
                representatives.get(mandate_types.PRESIDENT).append(mandataries)
            if mandataries.mandate.function == mandate_types.SECRETARY:
                representatives.get(mandate_types.SECRETARY).append(mandataries)
            if mandataries.mandate.function == mandate_types.SIGNATORY:
                representatives.get(mandate_types.SIGNATORY).append(mandataries)
    return representatives


def _convert_data_to_xls_row(education_group_year_data, header_list):
    xls_row = []
    for header in header_list:
        if header == SESSIONS_COLUMNS:
            session_datas = education_group_year_data.get(header, [])
            xls_row.extend(_convert_session_data_to_xls_row(session_datas))
        else:
            value = education_group_year_data.get(header, '')
            xls_row.append(value)
    return xls_row


def _convert_session_data_to_xls_row(session_datas):
    xls_session_rows = []
    for session_number in range(0, SESSIONS_NUMBER):
        session_formatted = _convert_data_to_xls_row(session_datas[session_number], SESSION_HEADERS)
        xls_session_rows.extend(session_formatted)
    return xls_session_rows


def _get_offer_year_calendar_from_prefetched_data(an_education_group_year: EducationGroupYear,
                                                  academic_calendar_type,
                                                  session_number=None):
    offer_year_cals = _get_all_offer_year_calendar_from_prefetched_data(
        an_education_group_year,
        academic_calendar_type
    )
    if session_number:
        offer_year_cals = [
            offer_year_cal for offer_year_cal in offer_year_cals
            if offer_year_cal.academic_calendar.sessionexamcalendar and
            offer_year_cal.academic_calendar.sessionexamcalendar.number_session == session_number
        ]

    if len(offer_year_cals) > 1:
        raise MultipleObjectsReturned
    return offer_year_cals[0] if offer_year_cals else None


def _get_all_offer_year_calendar_from_prefetched_data(an_education_group_year: EducationGroupYear,
                                                      academic_calendar_type) -> List:
    return [
        offer_year_calendar for offer_year_calendar in an_education_group_year.offeryearcalendar_set.all()
        if offer_year_calendar.academic_calendar.reference == academic_calendar_type
    ]


def _format_date(obj, date_key, date_form) -> str:
    date = getattr(obj, date_key, None) if obj else None
    if date:
        return date.strftime(date_form)
    return '-'


def _is_valid_mandate(mandate, education_group_yr: EducationGroupYear):
    return mandate.start_date <= education_group_yr.academic_year.start_date and \
           mandate.end_date >= education_group_yr.academic_year.end_date


def names(representatives) -> str:
    return ', '.join(sorted(str(mandatory.person.full_name) for mandatory in representatives))


def qualification(signatories) -> str:
    return ', '.join(sorted(signatory.mandate.qualification for signatory in signatories
                            if signatory.mandate.qualification))


def has_coorganization(education_group_year: EducationGroupYear) -> bool:
    return education_group_year.education_group_type.category == "TRAINING" and \
           education_group_year.education_group_type.name not in [
               TrainingType.PGRM_MASTER_120.name,
               TrainingType.PGRM_MASTER_180_240.name
           ]


def _get_title(a_version, language):
    title = a_version.title_fr
    if language == LANGUAGE_CODE_EN and a_version.title_en:
        title = a_version.title_en

    return " [{}]".format(title) if title else ''
