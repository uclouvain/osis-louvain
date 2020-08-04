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

from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business.education_group import can_user_edit_administrative_data, prepare_xls_content, create_xls, \
    XLS_DESCRIPTION, XLS_FILENAME, WORKSHEET_TITLE, EDUCATION_GROUP_TITLES, ORDER_COL, ORDER_DIRECTION, \
    XLS_DESCRIPTION_ADMINISTRATIVE, XLS_FILENAME_ADMINISTRATIVE, WORKSHEET_TITLE_ADMINISTRATIVE, \
    EDUCATION_GROUP_TITLES_ADMINISTRATIVE, prepare_xls_content_administrative, create_xls_administrative_data, \
    DATE_FORMAT, MANAGEMENT_ENTITY_COL, TRANING_COL, TYPE_COL, ACADEMIC_YEAR_COL, START_COURSE_REGISTRATION_COL, \
    END_COURSE_REGISTRATION_COL, SESSIONS_COLUMNS, WEIGHTING_COL, DEFAULT_LEARNING_UNIT_ENROLLMENT_COL, \
    CHAIR_OF_THE_EXAM_BOARD_COL, EXAM_BOARD_SECRETARY_COL, EXAM_BOARD_SIGNATORY_COL, SIGNATORY_QUALIFICATION_COL, \
    START_EXAM_REGISTRATION_COL, END_EXAM_REGISTRATION_COL, MARKS_PRESENTATION_COL, DISSERTATION_PRESENTATION_COL, \
    DELIBERATION_COL, SCORES_DIFFUSION_COL, SESSION_HEADERS, _get_translated_header_titles
from base.business.education_groups.perms import get_education_group_year_eligible_management_entities
from education_group.models.group_year import GroupYear

from base.models.enums import academic_calendar_type
from base.models.enums import education_group_categories
from base.models.enums import mandate_type as mandate_types
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.mandatary import MandataryFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.user import UserFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from osis_common.document import xls_build

NO_SESSION_DATA = {'session1': None, 'session2': None, 'session3': None}


class EducationGroupTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        # Create structure
        cls._create_basic_entity_structure()

        cls.academic_year = AcademicYearFactory(current=True)
        cls.education_group_year = EducationGroupYearFactory(
            management_entity=cls.chim_entity,
            academic_year=cls.academic_year
        )

    @classmethod
    def _create_basic_entity_structure(cls):
        cls.organization = OrganizationFactory()
        # Create entities UCL
        cls.root_entity = _create_entity_and_version_related_to(cls.organization, "UCL")
        # SST entity
        cls.sst_entity = _create_entity_and_version_related_to(cls.organization, "SST", cls.root_entity)
        cls.agro_entity = _create_entity_and_version_related_to(cls.organization, "AGRO", cls.sst_entity)
        cls.chim_entity = _create_entity_and_version_related_to(cls.organization, "CHIM", cls.sst_entity)

    def test_can_user_edit_administrative_data_with_permission_no_pgrm_manager(self):
        """With permission but no program manager of education group ==> Refused"""
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administrative_data_with_permission_and_pgrm_manager(self):
        """With permission and program manager of education group ==> Allowed"""
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked(self):
        """With permission + Group central manager + No linked to the right entity + Not program manager ==> Refused """
        CentralManagerFactory(person=self.person)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_entity_linked(self):
        """With permission + Group central manager + Linked to the right entity ==> Allowed """
        CentralManagerFactory(person=self.person, entity=self.education_group_year.management_entity)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_with_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child TRUE) ==> Allowed """
        CentralManagerFactory(person=self.person, entity=self.root_entity, with_child=True)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_no_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child FALSE) ==> Refused """
        CentralManagerFactory(person=self.person, entity=self.root_entity, with_child=False)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked_but_program_manager(self):
        """
        With permission + Group central manager + Linked to the parent entity (with_child FALSE) + IS
        program manager ==> Allowed
        """
        CentralManagerFactory(person=self.person, entity=self.root_entity, with_child=False)
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))


def _create_entity_and_version_related_to(organization, acronym, parent=None):
    entity = EntityFactory(organization=organization)
    EntityVersionFactory(acronym=acronym, entity=entity, parent=parent, end_date=None)
    return entity


def _add_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)


class EducationGroupXlsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()

    def setUp(self):
        self.education_group_type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        self.education_group_year_1 = EducationGroupYearFactory(academic_year=self.academic_year, acronym="PREMIER")
        self.education_group_year_1.management_entity_version = EntityVersionFactory()
        self.education_group_year_2 = EducationGroupYearFactory(academic_year=self.academic_year, acronym="DEUXIEME")
        self.education_group_year_2.management_entity_version = EntityVersionFactory()
        self.user = UserFactory()

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(prepare_xls_content([]), [])

    def test_prepare_xls_content_with_data(self):
        data = prepare_xls_content([self.education_group_year_1])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], get_xls_data(self.education_group_year_1))

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        create_xls(self.user, [], None, {ORDER_COL: None, ORDER_DIRECTION: None})

        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_asc_ordering(self, mock_generate_xls):
        create_xls(self.user,
                   [self.education_group_year_1, self.education_group_year_2],
                   None,
                   {ORDER_COL: 'acronym', ORDER_DIRECTION: None})

        xls_data = [get_xls_data(self.education_group_year_2), get_xls_data(self.education_group_year_1)]

        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_desc_ordering(self, mock_generate_xls):
        create_xls(self.user,
                   [self.education_group_year_1, self.education_group_year_2],
                   None,
                   {ORDER_COL: 'acronym', ORDER_DIRECTION: 'desc'})

        xls_data = [get_xls_data(self.education_group_year_1), get_xls_data(self.education_group_year_2)]

        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)


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
        EducationGroupVersionFactory(offer=cls.education_group_year_1, root_group__academic_year=cls.academic_year)

        cls.user = UserFactory()

    def setUp(self):
        self._create_administrative_data()
        self._create_mandatary_data()

    def _create_administrative_data(self):
        # Course enrollment event
        self.offer_yr_cal_course_enrollment = OfferYearCalendarFactory(
            academic_calendar__academic_year=self.academic_year,
            academic_calendar__reference=academic_calendar_type.COURSE_ENROLLMENT,
            education_group_year=self.education_group_year_1,
            start_date=datetime.datetime(2017, 9, 11, hour=4),
            end_date=datetime.datetime(2017, 9, 22, hour=6)
        )
        # Score submission event (session 1)
        self.offer_yr_cal_score_exam_submission_1 = OfferYearCalendarFactory(
            academic_calendar__academic_year=self.academic_year,
            academic_calendar__reference=academic_calendar_type.SCORES_EXAM_SUBMISSION,
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
            academic_calendar__academic_year=self.academic_year,
            academic_calendar__reference=academic_calendar_type.SCORES_EXAM_SUBMISSION,
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
        self.assertEqual(prepare_xls_content_administrative([]), [])

    def test_prepare_xls_content_administrative_with_data(self):
        data = prepare_xls_content_administrative([self.education_group_year_1])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], self.get_xls_administrative_data(self.education_group_year_1))

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        qs_empty = GroupYear.objects.none()
        create_xls_administrative_data(self.user, qs_empty, None, {ORDER_COL: None, ORDER_DIRECTION: None})

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

    def get_xls_administrative_data(self, an_education_group_year):
        return [
            an_education_group_year.management_entity_version.acronym,
            an_education_group_year.acronym,
            an_education_group_year.education_group_type,
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


def get_xls_data(an_education_group_year):
    return [an_education_group_year.academic_year.name,
            an_education_group_year.acronym,
            an_education_group_year.title,
            an_education_group_year.education_group_type,
            an_education_group_year.management_entity_version.acronym,
            an_education_group_year.partial_acronym]


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: EDUCATION_GROUP_TITLES,
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.FONT_ROWS: None,
            xls_build.ROW_HEIGHT: None,
        }]
    }


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
        }]
    }


class EducationGroupGetEligibleEntities(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def test_case_one_egy(self):
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        self.assertEqual(
            get_education_group_year_eligible_management_entities(education_group_year),
            [education_group_year.management_entity]
        )

    def test_case_one_egy_and_parent(self):
        education_group_year_child = EducationGroupYearFactory(academic_year=self.academic_year)
        education_group_year_parent = EducationGroupYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(
            parent=education_group_year_parent,
            child_branch=education_group_year_child
        )

        self.assertEqual(
            get_education_group_year_eligible_management_entities(education_group_year_child),
            [education_group_year_child.management_entity]
        )

        self.assertEqual(
            get_education_group_year_eligible_management_entities(education_group_year_parent),
            [education_group_year_parent.management_entity]
        )

    def test_case_one_egy_one_parent_no_entity_on_child(self):
        education_group_year_child = EducationGroupYearFactory(academic_year=self.academic_year)
        education_group_year_parent = EducationGroupYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(
            parent=education_group_year_parent,
            child_branch=education_group_year_child
        )
        education_group_year_child.management_entity = None
        education_group_year_child.save()

        self.assertEqual(
            get_education_group_year_eligible_management_entities(education_group_year_child),
            [education_group_year_parent.management_entity]
        )

    def test_case_one_egy_two_parent_no_entity_on_child(self):
        education_group_year_child = EducationGroupYearFactory(academic_year=self.academic_year)
        education_group_year_parent1 = EducationGroupYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(
            parent=education_group_year_parent1,
            child_branch=education_group_year_child
        )
        education_group_year_parent2 = EducationGroupYearFactory(academic_year=self.academic_year)
        GroupElementYearFactory(
            parent=education_group_year_parent2,
            child_branch=education_group_year_child
        )
        education_group_year_child.management_entity = None
        education_group_year_child.save()

        self.assertCountEqual(
            get_education_group_year_eligible_management_entities(education_group_year_child),
            [
                education_group_year_parent1.management_entity,
                education_group_year_parent2.management_entity,
            ]
        )

    def test_case_complex_hierarchy(self):
        education_group_year_child = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_child.management_entity, acronym="CHILD")

        education_group_year_parent1 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent1.management_entity, acronym="PARENT1")
        GroupElementYearFactory(
            parent=education_group_year_parent1,
            child_branch=education_group_year_child
        )

        education_group_year_parent2 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent2.management_entity, acronym="PARENT2")
        GroupElementYearFactory(
            parent=education_group_year_parent2,
            child_branch=education_group_year_child
        )

        education_group_year_parent3 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent3.management_entity, acronym="PARENT3")
        GroupElementYearFactory(
            parent=education_group_year_parent3,
            child_branch=education_group_year_parent1
        )

        education_group_year_parent4 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent4.management_entity, acronym="PARENT4")
        GroupElementYearFactory(
            parent=education_group_year_parent4,
            child_branch=education_group_year_parent1
        )

        education_group_year_parent5 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent5.management_entity, acronym="PARENT5")
        GroupElementYearFactory(
            parent=education_group_year_parent5,
            child_branch=education_group_year_child
        )
        GroupElementYearFactory(
            parent=education_group_year_parent5,
            child_branch=education_group_year_parent2
        )

        education_group_year_parent6 = EducationGroupYearFactory(academic_year=self.academic_year)
        EntityVersionFactory(entity=education_group_year_parent6.management_entity, acronym="PARENT6")
        GroupElementYearFactory(
            parent=education_group_year_parent6,
            child_branch=education_group_year_parent5
        )

        education_group_year_child.management_entity = None
        education_group_year_child.save()
        education_group_year_parent1.management_entity = None
        education_group_year_parent1.save()
        education_group_year_parent5.management_entity = None
        education_group_year_parent5.save()

        self.assertCountEqual(
            get_education_group_year_eligible_management_entities(education_group_year_child),
            [
                education_group_year_parent2.management_entity,
                education_group_year_parent3.management_entity,
                education_group_year_parent4.management_entity,
                education_group_year_parent6.management_entity,
            ]
        )
