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
import datetime
from unittest import mock

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business.education_group import ORDER_COL, ORDER_DIRECTION, \
    XLS_DESCRIPTION_ADMINISTRATIVE, XLS_FILENAME_ADMINISTRATIVE, WORKSHEET_TITLE_ADMINISTRATIVE, \
    EDUCATION_GROUP_TITLES_ADMINISTRATIVE, prepare_xls_content_administrative, create_xls_administrative_data, \
    DATE_FORMAT, MANAGEMENT_ENTITY_COL, TRANING_COL, TYPE_COL, ACADEMIC_YEAR_COL, START_COURSE_REGISTRATION_COL, \
    END_COURSE_REGISTRATION_COL, SESSIONS_COLUMNS, WEIGHTING_COL, DEFAULT_LEARNING_UNIT_ENROLLMENT_COL, \
    CHAIR_OF_THE_EXAM_BOARD_COL, EXAM_BOARD_SECRETARY_COL, EXAM_BOARD_SIGNATORY_COL, SIGNATORY_QUALIFICATION_COL, \
    START_EXAM_REGISTRATION_COL, END_EXAM_REGISTRATION_COL, MARKS_PRESENTATION_COL, DISSERTATION_PRESENTATION_COL, \
    DELIBERATION_COL, SCORES_DIFFUSION_COL, SESSION_HEADERS, _get_translated_header_titles, _extract_main_data
from base.models.enums import education_group_categories
from base.models.enums import mandate_type as mandate_types
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.mandatary import MandataryFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.user import UserFactory
from education_group.models.group_year import GroupYear
from osis_common.document import xls_build
from program_management.tests.factories.education_group_version import \
    ParticularTransitionEducationGroupVersionFactory, StandardEducationGroupVersionFactory

LANGUAGE_CODE_FR = "fr-be"

NO_SESSION_DATA = {'session1': None, 'session2': None, 'session3': None}


class EducationGroupXlsAdministrativeDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.next_academic_year = AcademicYearFactory(year=cls.academic_year.year + 1)
        cls.education_group_type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        cls.education_group = EducationGroupFactory(start_year=cls.academic_year,
                                                    end_year=cls.next_academic_year)
        cls.education_group_year_1 = EducationGroupYearFactory(academic_year=cls.academic_year, acronym="PREMIER",
                                                               education_group=cls.education_group,
                                                               weighting=True)
        cls.education_group_year_1.management_entity_version = EntityVersionFactory()
        cls.version = StandardEducationGroupVersionFactory(offer=cls.education_group_year_1,
                                                           root_group__academic_year=cls.academic_year)

        cls.user = UserFactory()

    def setUp(self):
        self._create_administrative_data()
        self._create_mandatary_data()

    def _create_administrative_data(self):
        # Course enrollment event
        self.offer_yr_cal_course_enrollment = OfferYearCalendarFactory(
            academic_calendar__data_year=self.academic_year,
            academic_calendar__reference=AcademicCalendarTypes.COURSE_ENROLLMENT.name,
            education_group_year=self.education_group_year_1,
            start_date=datetime.datetime(2017, 9, 11, hour=4),
            end_date=datetime.datetime(2017, 9, 22, hour=6)
        )
        # Score submission event (session 1)
        self.offer_yr_cal_score_exam_submission_1 = OfferYearCalendarFactory(
            academic_calendar__data_year=self.academic_year,
            academic_calendar__reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
            education_group_year=self.education_group_year_1,
            start_date=datetime.datetime(2017, 5, 11, hour=4),
            end_date=datetime.datetime(2017, 5, 22, hour=6)
        )
        SessionExamCalendarFactory(
            academic_calendar=self.offer_yr_cal_score_exam_submission_1.academic_calendar,
            number_session=1
        )
        # Score submission event (session 2)
        self.offer_yr_cal_score_exam_submission_2 = OfferYearCalendarFactory(
            academic_calendar__data_year=self.academic_year,
            academic_calendar__reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name,
            education_group_year=self.education_group_year_1,
            start_date=datetime.datetime(2017, 9, 1, hour=4)
        )
        SessionExamCalendarFactory(
            academic_calendar=self.offer_yr_cal_score_exam_submission_2.academic_calendar,
            number_session=2
        )

    def _create_mandatary_data(self):
        self.president = MandataryFactory(
            mandate__education_group=self.education_group,
            mandate__function=mandate_types.PRESIDENT,
            mandate__qualification=None,
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date
        )
        self.secretary_1 = MandataryFactory(
            mandate__education_group=self.education_group,
            mandate__function=mandate_types.SECRETARY,
            mandate__qualification=None,
            person__last_name='Armand',
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date
        )
        self.secretary_2 = MandataryFactory(
            mandate__education_group=self.education_group,
            mandate__function=mandate_types.SECRETARY,
            mandate__qualification=None,
            person__last_name='Durant',
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date
        )
        self.signatory = MandataryFactory(
            mandate__education_group=self.education_group,
            mandate__function=mandate_types.SIGNATORY,
            mandate__qualification='Responsable',
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date
        )

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(prepare_xls_content_administrative([], LANGUAGE_CODE_FR), [])

    def test_prepare_xls_content_administrative_with_data(self):
        data = prepare_xls_content_administrative([self.version], LANGUAGE_CODE_FR)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], self.get_xls_administrative_data())

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        qs_empty = GroupYear.objects.none()
        create_xls_administrative_data(self.user,
                                       qs_empty,
                                       None,
                                       {ORDER_COL: None, ORDER_DIRECTION: None},
                                       LANGUAGE_CODE_FR
                                       )

        expected_argument = _generate_xls_administrative_data_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    def test_headers_title_property(self):
        expected_headers = [
            MANAGEMENT_ENTITY_COL,
            TRANING_COL,
            TYPE_COL,
            ACADEMIC_YEAR_COL,
            START_COURSE_REGISTRATION_COL,
            END_COURSE_REGISTRATION_COL,
            SESSIONS_COLUMNS,
            WEIGHTING_COL,
            DEFAULT_LEARNING_UNIT_ENROLLMENT_COL,
            CHAIR_OF_THE_EXAM_BOARD_COL,
            EXAM_BOARD_SECRETARY_COL,
            EXAM_BOARD_SIGNATORY_COL,
            SIGNATORY_QUALIFICATION_COL
        ]
        expected_session_headers = [
            START_EXAM_REGISTRATION_COL,
            END_EXAM_REGISTRATION_COL,
            MARKS_PRESENTATION_COL,
            DISSERTATION_PRESENTATION_COL,
            DELIBERATION_COL,
            SCORES_DIFFUSION_COL
        ]
        self.assertEqual(EDUCATION_GROUP_TITLES_ADMINISTRATIVE, expected_headers)
        self.assertEqual(SESSION_HEADERS, expected_session_headers)

    def test_extract_main_data_with_non_standard_version(self):
        education_group_yr = EducationGroupYearFactory()
        education_group_yr.management_entity_version = EntityVersionFactory()

        a_version = ParticularTransitionEducationGroupVersionFactory(offer=education_group_yr)

        an_education_group_year = a_version.offer
        data = _extract_main_data(a_version, LANGUAGE_CODE_FR)

        self.assertEqual(
            data[TRANING_COL],
            "{}{}".format(an_education_group_year.acronym, "[{}-{}]".format(
                a_version.version_name, a_version.transition_name
            ))
        )
        self.assertEqual(data[TYPE_COL],
                         "{}{}".format(an_education_group_year.education_group_type, " [{}]".format(a_version.title_fr))
                         )

    def test_extract_main_data_with_standard_version(self):
        education_group_yr = EducationGroupYearFactory()
        education_group_yr.management_entity_version = EntityVersionFactory()

        a_version = StandardEducationGroupVersionFactory(offer=education_group_yr)

        an_education_group_year = a_version.offer
        data = _extract_main_data(a_version, LANGUAGE_CODE_FR)

        self.assertEqual(data[TRANING_COL], "{}".format(an_education_group_year.acronym)
                         )
        self.assertEqual(data[TYPE_COL],
                         "{}{}".format(an_education_group_year.education_group_type,
                                       " [{}]".format(a_version.title_fr) if a_version and a_version.title_fr else '')
                         )

    def get_xls_administrative_data(self):
        an_education_group_year = self.version.offer
        return [
            an_education_group_year.management_entity_version.acronym,
            an_education_group_year.acronym,
            "{}{}".format(
                an_education_group_year.education_group_type,
                " [{}]".format(self.version.title_fr) if self.version.title_fr else ''),
            an_education_group_year.academic_year.name,
            self.offer_yr_cal_course_enrollment.start_date.strftime(DATE_FORMAT),
            self.offer_yr_cal_course_enrollment.end_date.strftime(DATE_FORMAT),
            '-',
            '-',
            self.offer_yr_cal_score_exam_submission_1.start_date.strftime(DATE_FORMAT),
            '-',
            '-',
            '-',
            '-',
            '-',
            self.offer_yr_cal_score_exam_submission_2.start_date.strftime(DATE_FORMAT),
            '-',
            '-',
            '-',
            '-',
            '-',
            '-',
            '-',
            '-',
            '-',
            _('yes'),
            _('no'),
            str(self.president.person.full_name),
            '{}, {}'.format(str(self.secretary_1.person.full_name), str(self.secretary_2.person.full_name)),
            str(self.signatory.person.full_name),
            'Responsable'
        ]


def _generate_xls_administrative_data_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION_ADMINISTRATIVE),
        xls_build.FILENAME_KEY: _(XLS_FILENAME_ADMINISTRATIVE),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: _get_translated_header_titles(),
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE_ADMINISTRATIVE),
            xls_build.STYLED_CELLS: None,
            xls_build.FONT_ROWS: None,
            xls_build.ROW_HEIGHT: None,
            xls_build.FONT_CELLS: None,
            xls_build.BORDER_CELLS: None
        }]
    }
