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
import datetime
from unittest import mock

from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.business.education_group import can_user_edit_administrative_data, prepare_xls_content, create_xls, \
    XLS_DESCRIPTION, XLS_FILENAME, WORKSHEET_TITLE, EDUCATION_GROUP_TITLES, ORDER_COL, ORDER_DIRECTION, \
    XLS_DESCRIPTION_ADMINISTRATIVE, XLS_FILENAME_ADMINISTRATIVE, WORKSHEET_TITLE_ADMINISTRATIVE, \
    EDUCATION_GROUP_TITLES_ADMINISTRATIVE, prepare_xls_content_administrative, create_xls_administrative_data, \
    PRESIDENTS, SECRETARIES, SIGNATORIES, DATE_TIME_FORMAT, DATE_FORMAT

from base.models.enums import offer_year_entity_type
from base.models.person import Person, CENTRAL_MANAGER_GROUP
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory
from base.models.enums import education_group_categories
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.academic_year import create_current_academic_year
from osis_common.document import xls_build
from base.tests.factories.mandate import MandateFactory
from base.tests.factories.mandatary import MandataryFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.models.enums import mandate_type as mandate_types
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.models.enums import academic_calendar_type
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from django.test.utils import override_settings
NO_SESSION_DATA = {'session1': None, 'session2': None, 'session3': None}


class EducationGroupTestCase(TestCase):
    def setUp(self):
        # Get or Create Permission to edit administrative data
        content_type = ContentType.objects.get_for_model(Person)
        permission, created = Permission.objects.get_or_create(
            codename="can_edit_education_group_administrative_data",
            content_type=content_type)
        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(permission)
        # Create structure
        self._create_basic_entity_structure()
        # Create education group with 'CHIM' as entity management
        self.education_group_year = EducationGroupYearFactory()
        OfferYearEntityFactory(education_group_year=self.education_group_year,
                               type=offer_year_entity_type.ENTITY_MANAGEMENT,
                               entity=self.chim_entity)

    def test_can_user_edit_administrative_data_no_permission(self):
        """Without permission/group, we cannot access to administrative data ==> Refused"""
        user_without_perm = UserFactory()
        self.assertFalse(can_user_edit_administrative_data(user_without_perm, self.education_group_year))

    def test_can_user_edit_administrative_data_with_permission_no_pgrm_manager(self):
        """With permission but no program manager of education group ==> Refused"""
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administrative_data_with_permission_and_pgrm_manager(self):
        """With permission and program manager of education group ==> Allowed"""
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked(self):
        """With permission + Group central manager + No linked to the right entity + Not program manager ==> Refused """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_entity_linked(self):
        """With permission + Group central manager + Linked to the right entity ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.chim_entity, with_child=False)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_with_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child TRUE) ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=True)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_parent_entity_linked_no_child(self):
        """With permission + Group central manager + Linked to the parent entity (with child FALSE) ==> Refused """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=False)
        self.assertFalse(can_user_edit_administrative_data(self.user, self.education_group_year))

    def test_can_user_edit_administartive_data_group_central_manager_no_entity_linked_but_program_manager(self):
        """With permission + Group central manager + Linked to the parent entity (with_child FALSE) + IS program manager ==> Allowed """
        _add_to_group(self.user, CENTRAL_MANAGER_GROUP)
        PersonEntityFactory(person=self.person, entity=self.root_entity, with_child=False)
        ProgramManagerFactory(person=self.person, education_group=self.education_group_year.education_group)
        self.assertTrue(can_user_edit_administrative_data(self.user, self.education_group_year))

    def _create_basic_entity_structure(self):
        self.organization = OrganizationFactory(name="Université catholique de Louvain", acronym="UCL")
        # Create entities UCL
        self.root_entity = _create_entity_and_version_related_to(self.organization, "UCL")
        # SST entity
        self.sst_entity = _create_entity_and_version_related_to(self.organization, "SST", self.root_entity)
        self.agro_entity = _create_entity_and_version_related_to(self.organization, "AGRO", self.sst_entity)
        self.chim_entity = _create_entity_and_version_related_to(self.organization, "CHIM", self.sst_entity)


def _create_entity_and_version_related_to(organization, acronym, parent=None):
    entity = EntityFactory(organization=organization)
    EntityVersionFactory(acronym=acronym, entity=entity, parent=parent, end_date=None)
    return entity


def _add_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)


class EducationGroupXlsTestCase(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
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
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.education_group_type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        self.education_group = EducationGroupFactory(start_year=self.academic_year.year,
                                                     end_year=self.academic_year.year + 1)
        self.education_group_year_1 = EducationGroupYearFactory(academic_year=self.academic_year, acronym="PREMIER",
                                                                education_group=self.education_group,
                                                                weighting=True)
        self.education_group_year_1.management_entity_version = EntityVersionFactory()
        self.mandate_president = MandateFactory(education_group=self.education_group, function=mandate_types.PRESIDENT,
                                                qualification=None)
        self.president = MandataryFactory(mandate=self.mandate_president,
                                          start_date=self.academic_year.start_date,
                                          end_date=self.academic_year.end_date)
        self.secretary_1 = MandataryFactory(
            mandate=MandateFactory(education_group=self.education_group, function=mandate_types.SECRETARY,
                                   qualification=None),
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date)
        self.secretary_2 = MandataryFactory(
            mandate=MandateFactory(education_group=self.education_group, function=mandate_types.SECRETARY,
                                   qualification=None),
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date)
        self.signatory = MandataryFactory(
            mandate=MandateFactory(education_group=self.education_group, function=mandate_types.SIGNATORY,
                                   qualification='Responsable'),
            start_date=self.academic_year.start_date,
            end_date=self.academic_year.end_date)

        self.academic_cal_course_enrollment = AcademicCalendarFactory(
            academic_year=self.academic_year,
            reference=academic_calendar_type.COURSE_ENROLLMENT
        )
        OfferYearCalendarFactory(education_group_year=self.education_group_year_1,
                                 academic_calendar=self.academic_cal_course_enrollment)
        self.academic_cal_scores_exam_submission_1 = AcademicCalendarFactory(
            academic_year=self.academic_year,
            reference=academic_calendar_type.SCORES_EXAM_SUBMISSION
        )
        self.scores_exam_submission_2 = AcademicCalendarFactory(academic_year=self.academic_year,
                                                                reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.offer_yr_cal_score_exam_submission_1 = OfferYearCalendarFactory(
            education_group_year=self.education_group_year_1,
            academic_calendar=self.academic_cal_scores_exam_submission_1)

        self.offer_yr_cal_score_exam_submission_2 = OfferYearCalendarFactory(
            education_group_year=self.education_group_year_1,
            academic_calendar=self.scores_exam_submission_2)
        self.session_exam_cal_deliberation_1 = SessionExamCalendarFactory(
            academic_calendar=self.academic_cal_scores_exam_submission_1,
            number_session=1)
        self.session_exam_cal_deliberation_2 = SessionExamCalendarFactory(
            academic_calendar=self.scores_exam_submission_2,
            number_session=2)
        self.offer_yr_cal_score_exam_submission_1.start_date = datetime.date(2017, 9, 1)
        self.offer_yr_cal_score_exam_submission_1.save()
        self.education_group_year_1.administrative_data = {
            'course_enrollment': {'dates': self.academic_cal_course_enrollment},
            'exam_enrollments': NO_SESSION_DATA,
            'scores_exam_submission': {'session1': self.offer_yr_cal_score_exam_submission_1},
            'dissertation_submission': NO_SESSION_DATA,
            'deliberation': NO_SESSION_DATA,
            'scores_exam_diffusion': NO_SESSION_DATA,
            PRESIDENTS: [self.president],
            SECRETARIES: [self.secretary_1, self.secretary_2],
            SIGNATORIES: [self.signatory]}
        self.user = UserFactory()

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(prepare_xls_content_administrative([]), [])

    def test_prepare_xls_content_administrative_with_data(self):
        data = prepare_xls_content_administrative([self.education_group_year_1])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], self.get_xls_administrative_data(self.education_group_year_1))

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        create_xls_administrative_data(self.user, [], None, {ORDER_COL: None, ORDER_DIRECTION: None})

        expected_argument = _generate_xls_administrative_data_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    def get_xls_administrative_data(self, an_education_group_year):
        return [an_education_group_year.management_entity_version.acronym,
                an_education_group_year.acronym,
                an_education_group_year.education_group_type,
                an_education_group_year.academic_year.name,
                self.academic_cal_course_enrollment.start_date.strftime(DATE_FORMAT),
                self.academic_cal_course_enrollment.end_date.strftime(DATE_FORMAT),
                '-',
                '-',
                self.offer_yr_cal_score_exam_submission_1.start_date.strftime(DATE_TIME_FORMAT),
                '-',
                '-',
                '-',
                '-',
                '-',
                '-',
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
                str(self.president.person),
                '{}, {}'.format(str(self.secretary_1.person), str(self.secretary_2.person)),
                str(self.signatory.person),
                'Responsable']


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
        }]
    }


def _generate_xls_administrative_data_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION_ADMINISTRATIVE),
        xls_build.FILENAME_KEY: _(XLS_FILENAME_ADMINISTRATIVE),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: EDUCATION_GROUP_TITLES_ADMINISTRATIVE,
            xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE_ADMINISTRATIVE),
        }]
    }

