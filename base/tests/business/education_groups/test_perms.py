##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import random
from unittest import mock

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings

from base.business.education_groups.perms import check_permission, \
    check_authorized_type, is_eligible_to_edit_general_information, is_eligible_to_edit_admission_condition, \
    GeneralInformationPerms, CommonEducationGroupStrategyPerms, AdmissionConditionPerms, \
    _is_eligible_to_add_education_group_with_category, CertificateAimsPerms
from base.models.academic_calendar import get_academic_calendar_by_date_and_reference_and_data_year
from base.models.enums import academic_calendar_type
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.education_group_categories import TRAINING, Categories
from base.tests.factories.academic_calendar import AcademicCalendarFactory, OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, \
    EducationGroupYearCommonBachelorFactory, TrainingFactory, MiniTrainingFactory, GroupFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory, CentralManagerFactory, \
    SICFactory, FacultyManagerFactory, UEFacultyManagerFactory, AdministrativeManagerFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory, SuperUserFactory


class TestPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.current_academic_year)

    def test_has_person_the_right_to_add_education_group(self):
        person_without_right = PersonFactory()
        self.assertFalse(check_permission(person_without_right, "base.add_educationgroup"))

        person_with_right = PersonWithPermissionsFactory("add_educationgroup")
        self.assertTrue(check_permission(person_with_right, "base.add_educationgroup"))

    def test_is_education_group_edit_period_opened_case_period_closed(self):
        today = datetime.date.today()

        AcademicCalendarFactory(
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            data_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertIsNone(get_academic_calendar_by_date_and_reference_and_data_year(
                self.education_group_year.academic_year, academic_calendar_type.EDUCATION_GROUP_EDITION))

    def test_is_education_group_edit_period_opened_case_period_opened(self):
        today = datetime.date.today()

        aca_calendar = AcademicCalendarFactory(
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            data_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertEqual(aca_calendar, get_academic_calendar_by_date_and_reference_and_data_year(
            self.education_group_year.academic_year, academic_calendar_type.EDUCATION_GROUP_EDITION))

    def test_is_education_group_edit_period_opened_case_period_opened_but_not_same_academic_year(self):
        today = datetime.date.today()
        EducationGroupYearFactory(academic_year__year=self.current_academic_year.year + 1)

        AcademicCalendarFactory(
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            data_year__year=self.current_academic_year.year+1,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertIsNone(get_academic_calendar_by_date_and_reference_and_data_year(
            self.education_group_year.academic_year, academic_calendar_type.EDUCATION_GROUP_EDITION))

    def test_check_unauthorized_type(self):
        education_group = EducationGroupYearFactory()
        result = check_authorized_type(education_group, Categories.TRAINING)
        self.assertFalse(result)

    def test_check_authorized_type(self):
        education_group = EducationGroupYearFactory()
        AuthorizedRelationshipFactory(parent_type=education_group.education_group_type)
        result = check_authorized_type(education_group, Categories.TRAINING)
        self.assertTrue(result)

    def test_check_authorized_type_without_parent(self):
        result = check_authorized_type(None, TRAINING)
        self.assertTrue(result)

    def test_faculty_manager_is_not_eligible_to_add_groups_in_search_page(self):
        result = _is_eligible_to_add_education_group_with_category(
            FacultyManagerFactory(),
            None,
            Categories.GROUP,
            raise_exception=False
        )
        self.assertFalse(result)

    def test_faculty_manager_is_eligible_to_add_groups_in_tree_of_offer_of_its_entity(self):
        result = _is_eligible_to_add_education_group_with_category(
            FacultyManagerFactory(),
            EducationGroupYearFactory(),
            Categories.GROUP,
            raise_exception=False
        )
        self.assertTrue(result)

    def test_faculty_manager_is_eligible_to_add_mini_training(self):
        result = _is_eligible_to_add_education_group_with_category(
            FacultyManagerFactory(),
            random.choice([EducationGroupYearFactory(), None]),
            Categories.MINI_TRAINING,
            raise_exception=False
        )
        self.assertTrue(result)

    def test_faculty_manager_is_not_eligible_to_add_training(self):
        result = _is_eligible_to_add_education_group_with_category(
            FacultyManagerFactory(),
            random.choice([EducationGroupYearFactory(), None]),
            Categories.TRAINING,
            raise_exception=False
        )
        self.assertFalse(result)


@override_settings(YEAR_LIMIT_EDG_MODIFICATION=2019)
class TestCommonEducationGroupStrategyPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory()
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=cls.current_academic_year,
                                    data_year=cls.current_academic_year)
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION,
                                    academic_year__year=cls.current_academic_year.year + 1,
                                    data_year=AcademicYearFactory(year=cls.current_academic_year.year + 1))
        for year in range(cls.current_academic_year.year - 10, cls.current_academic_year.year + 10):
            AcademicYearFactory(year=year)

    def test_person_property(self):
        person = PersonWithPermissionsFactory()
        perm = CommonEducationGroupStrategyPerms(person.user, TrainingFactory())
        self.assertEqual(perm.person, person)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible",
                side_effect=PermissionDenied())
    def test_is_eligible_case_no_raising_exception(self, mock_is_eligible):
        person = PersonWithPermissionsFactory()
        perm = CommonEducationGroupStrategyPerms(person.user, TrainingFactory())

        self.assertFalse(perm.is_eligible(raise_exception=False))

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible",
                side_effect=PermissionDenied())
    def test_is_eligible_case_raising_exception(self, mock_is_eligible):
        person = PersonWithPermissionsFactory()
        perm = CommonEducationGroupStrategyPerms(person.user, TrainingFactory())

        with self.assertRaises(PermissionDenied):
            perm.is_eligible(raise_exception=True)

    def test_is_lower_than_limit_edg_year_case_lower(self):
        """This test ensure that we cannot modify OF which lower than limit year"""
        training_lower = TrainingFactory(academic_year__year=settings.YEAR_LIMIT_EDG_MODIFICATION - 1)

        perm = CommonEducationGroupStrategyPerms(self.person.user, training_lower)
        self.assertTrue(perm._is_lower_than_limit_edg_year())

    def test_is_lower_than_limit_edg_year_case_greater(self):
        """This test ensure that we modify OF which greater or equal than limit year"""
        training_limit_year = TrainingFactory(academic_year__year=settings.YEAR_LIMIT_EDG_MODIFICATION + 1)
        training_greater = TrainingFactory(academic_year__year=settings.YEAR_LIMIT_EDG_MODIFICATION)

        for education_group_year in [training_limit_year, training_greater]:
            with self.subTest(msg=education_group_year):
                perm = CommonEducationGroupStrategyPerms(self.person.user, education_group_year)
                self.assertFalse(perm._is_lower_than_limit_edg_year())

    @mock.patch('base.business.education_groups.perms.check_link_to_management_entity', return_value=True)
    def test_is_linked_to_management_entity(self, mock_check_link):
        training = TrainingFactory()
        perm = CommonEducationGroupStrategyPerms(self.person.user, training)

        self.assertTrue(perm._is_linked_to_management_entity())
        self.assertTrue(mock_check_link.called)

    def test_is_eligible_case_user_as_superuser_case_greater_or_equal_limit_year(self):
        super_user = UserFactory(is_superuser=True)
        training = TrainingFactory(academic_year__year=settings.YEAR_LIMIT_EDG_MODIFICATION)

        perm = CommonEducationGroupStrategyPerms(super_user, training)
        self.assertTrue(perm._is_eligible())

    def test_is_eligible_case_user_as_superuser_case_lower_than_limit_year(self):
        super_user = UserFactory(is_superuser=True)
        training = TrainingFactory(academic_year__year=settings.YEAR_LIMIT_EDG_MODIFICATION - 1)

        perm = CommonEducationGroupStrategyPerms(super_user, training)
        with self.assertRaises(PermissionDenied):
            perm._is_eligible()

    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_lower_than_limit_edg_year",
        return_value=False)
    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_linked_to_management_entity",
        return_value=True)
    def test_ensure_is_eligible_case_all_submethod_true(self, mock_linked_to_management, mock_limit_egy_year):
        perm = CommonEducationGroupStrategyPerms(self.person.user, TrainingFactory())

        self.assertTrue(perm._is_eligible())
        self.assertTrue(mock_linked_to_management.called)
        self.assertTrue(mock_limit_egy_year.called)

    @mock.patch(
        "base.models.academic_calendar.get_academic_calendar_by_date_and_reference_and_data_year",
        return_value=False)
    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_linked_to_management_entity",
        return_value=True)
    def test_ensure_is_eligible_case_permission_denied(self, mock_linked_to_management, mock_is_current_in_range):
        perm = CommonEducationGroupStrategyPerms(self.person.user, TrainingFactory())

        with self.assertRaises(PermissionDenied):
            perm._is_eligible()

    @mock.patch(
        "base.models.academic_calendar.get_academic_calendar_by_date_and_reference_and_data_year",
        return_value=True)
    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_linked_to_management_entity",
        return_value=False)
    def test_ensure_is_eligible_case_permission_denied(self, mock_linked_to_management, mock_is_current_in_range):
        perm = CommonEducationGroupStrategyPerms(self.person.user, TrainingFactory())

        with self.assertRaises(PermissionDenied):
            perm._is_eligible()


class TestGeneralInformationPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        OpenAcademicCalendarFactory(reference=EDUCATION_GROUP_EDITION, academic_year=cls.current_academic_year,
                                    data_year=cls.current_academic_year)
        cls.common_bachelor = EducationGroupYearCommonBachelorFactory(academic_year=cls.current_academic_year)
        cls.training = TrainingFactory(academic_year=cls.current_academic_year)

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_is_eligible_to_edit_general_information(self, mock_is_eligible):
        person = PersonWithPermissionsFactory()

        self.assertTrue(is_eligible_to_edit_general_information(person, self.common_bachelor))
        self.assertTrue(mock_is_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_central_manager_eligible")
    def test_is_eligible_case_user_is_central_manager(self, mock_is_central_eligible, mock_user_have_perm,
                                                      mock_super_is_eligible):
        central_manager = CentralManagerFactory()
        perm = GeneralInformationPerms(central_manager.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_central_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_faculty_manager_eligible")
    def test_is_eligible_case_user_is_faculty_manager(self, mock_is_faculty_eligible, mock_user_have_perm,
                                                      mock_super_is_eligible):
        faculty_manager = FacultyManagerFactory()
        perm = GeneralInformationPerms(faculty_manager.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_faculty_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    def test_is_not_eligible_case_user_is_faculty_manager_for_ue(self, mock_super_is_eligible):
        faculty_manager = UEFacultyManagerFactory()
        perm = GeneralInformationPerms(faculty_manager.user, self.common_bachelor)
        with self.assertRaises(PermissionDenied):
            perm._is_eligible()
        self.assertTrue(mock_super_is_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms._is_sic_eligible")
    def test_is_eligible_case_user_is_sic(self, mock_is_sic_eligible, mock_user_have_perm, mock_super_is_eligible):
        sic = SICFactory()
        perm = GeneralInformationPerms(sic.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_sic_eligible.called)

    def test_is_not_eligible_case_user_is_administrative_manager(self, ):
        administrative_manager = AdministrativeManagerFactory()

        perm = GeneralInformationPerms(administrative_manager.user, self.common_bachelor)
        self.assertFalse(perm.is_eligible())

    def test_is_user_have_perm_for_common_case_user_without_perm(self):
        person = PersonWithPermissionsFactory()

        perm = GeneralInformationPerms(person.user, self.common_bachelor)
        self.assertFalse(perm._is_user_have_perm())

    def test_is_user_have_perm_for_common_case_user_with_perm(self):
        person = PersonWithPermissionsFactory("change_commonpedagogyinformation")

        perm = GeneralInformationPerms(person.user, self.common_bachelor)
        self.assertTrue(perm._is_user_have_perm())

    def test_is_user_have_perm_for_non_common_case_user_without_perm(self):
        person = PersonWithPermissionsFactory()

        perm = GeneralInformationPerms(person.user, self.training)
        self.assertFalse(perm._is_user_have_perm())

    def test_is_user_have_perm_for_non_common_case_user_with_perm(self):
        person = PersonWithPermissionsFactory("change_pedagogyinformation")

        perm = GeneralInformationPerms(person.user, self.training)
        self.assertTrue(perm._is_user_have_perm())

    def test_is_central_manager_eligible(self):
        central_manager = CentralManagerFactory()

        for education_group_year in [self.common_bachelor, self.training]:
            perm = GeneralInformationPerms(central_manager.user, education_group_year)
            self.assertTrue(perm._is_central_manager_eligible())

    def test_is_sic_eligible(self):
        sic_manager = SICFactory()

        for education_group_year in [self.common_bachelor, self.training]:
            perm = GeneralInformationPerms(sic_manager.user, education_group_year)
            self.assertTrue(perm._is_sic_eligible())

    def test_is_faculty_manager_eligible(self):
        faculty_manager = FacultyManagerFactory()

        for education_group_year in [self.training, self.common_bachelor]:
            with self.subTest(msg=education_group_year):
                perm = GeneralInformationPerms(faculty_manager.user, education_group_year)
                self.assertTrue(perm._is_faculty_manager_eligible())


class TestAdmissionConditionPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.common_bachelor = EducationGroupYearCommonBachelorFactory(academic_year=cls.current_academic_year)
        cls.training = TrainingFactory(academic_year=cls.current_academic_year)

    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms.is_eligible", return_value=True)
    def test_is_eligible_to_edit_general_information(self, mock_is_eligible):
        person = PersonWithPermissionsFactory()

        self.assertTrue(is_eligible_to_edit_admission_condition(person, self.common_bachelor))
        self.assertTrue(mock_is_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_central_manager_eligible")
    def test_is_eligible_case_user_is_central_manager(self, mock_is_central_eligible, mock_user_have_perm,
                                                      mock_super_is_eligible):
        central_manager = CentralManagerFactory()
        perm = AdmissionConditionPerms(central_manager.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_central_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_faculty_manager_eligible")
    def test_is_eligible_case_user_is_faculty_manager(self, mock_is_faculty_eligible, mock_user_have_perm,
                                                      mock_super_is_eligible):
        faculty_manager = FacultyManagerFactory()
        perm = AdmissionConditionPerms(faculty_manager.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_faculty_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    def test_is_not_eligible_case_user_is_faculty_manager_for_ue(self, mock_super_is_eligible):
        faculty_manager = UEFacultyManagerFactory()
        perm = AdmissionConditionPerms(faculty_manager.user, self.common_bachelor)
        with self.assertRaises(PermissionDenied):
            perm._is_eligible()
        self.assertTrue(mock_super_is_eligible.called)

    @mock.patch("base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_eligible")
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_user_have_perm", return_value=True)
    @mock.patch("base.business.education_groups.perms.AdmissionConditionPerms._is_sic_eligible")
    def test_is_eligible_case_user_is_sic(self, mock_is_sic_eligible, mock_user_have_perm, mock_super_is_eligible):
        sic = SICFactory()
        perm = AdmissionConditionPerms(sic.user, self.common_bachelor)
        perm._is_eligible()

        self.assertTrue(mock_super_is_eligible.called)
        self.assertTrue(mock_is_sic_eligible.called)

    def test_is_not_eligible_case_user_is_administrative_manager(self, ):
        administrative_manager = AdministrativeManagerFactory()

        perm = AdmissionConditionPerms(administrative_manager.user, self.common_bachelor)
        self.assertFalse(perm.is_eligible())

    def test_is_user_have_perm_for_common_case_user_without_perm(self):
        person = PersonWithPermissionsFactory()

        perm = AdmissionConditionPerms(person.user, self.common_bachelor)
        self.assertFalse(perm._is_user_have_perm())

    def test_is_user_have_perm_for_common_case_user_with_perm(self):
        person = PersonWithPermissionsFactory("change_commonadmissioncondition")

        perm = AdmissionConditionPerms(person.user, self.common_bachelor)
        self.assertTrue(perm._is_user_have_perm())

    def test_is_user_have_perm_for_non_common_case_user_without_perm(self):
        person = PersonWithPermissionsFactory()

        perm = AdmissionConditionPerms(person.user, self.training)
        self.assertFalse(perm._is_user_have_perm())

    def test_is_user_have_perm_for_non_common_case_user_with_perm(self):
        person = PersonWithPermissionsFactory("change_admissioncondition")

        perm = AdmissionConditionPerms(person.user, self.training)
        self.assertTrue(perm._is_user_have_perm())

    def test_is_faculty_manager_case_cannot_modify_data_in_past(self):
        previous_year = self.current_academic_year.year - 1

        training_in_past = TrainingFactory(academic_year__year=previous_year)
        common_in_past = EducationGroupYearCommonBachelorFactory(academic_year__year=previous_year)
        faculty_manager = FacultyManagerFactory()

        for education_group_year in [training_in_past, common_in_past]:
            perm = AdmissionConditionPerms(faculty_manager.user, education_group_year)
            with self.assertRaises(PermissionDenied):
                perm._is_faculty_manager_eligible()

    @mock.patch("base.models.academic_calendar.get_academic_calendar_by_date_and_reference_and_data_year",
                return_value=False)
    def test_is_faculty_manager_case_cannot_modify_data_outside_period(self, mock_calendar_opened):
        person = PersonWithPermissionsFactory()

        perm = AdmissionConditionPerms(person.user, self.training)
        with self.assertRaises(PermissionDenied):
            perm._is_eligible()


class TestCertificateAimsPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2019)
        cls.training = TrainingFactory(academic_year=cls.academic_year)

    def test_user_is_not_program_manager(self):
        person = PersonFactory()
        perm = CertificateAimsPerms(user=person.user, education_group_year=self.training)
        self.assertFalse(perm.is_eligible())

    def test_user_is_program_manager_but_not_of_the_education_group_year(self):
        program_manager = ProgramManagerFactory()
        perm = CertificateAimsPerms(user=program_manager.person.user, education_group_year=self.training)
        self.assertFalse(perm.is_eligible())

    def test_user_is_program_manager_of_the_education_group_year(self):
        program_manager = ProgramManagerFactory(education_group=self.training.education_group)
        perm = CertificateAimsPerms(user=program_manager.person.user, education_group_year=self.training)
        self.assertTrue(perm.is_eligible())

    def test_user_is_super_user(self):
        super_user = SuperUserFactory()
        perm = CertificateAimsPerms(user=super_user, education_group_year=self.training)
        self.assertTrue(perm.is_eligible())

    def test_education_group_year_is_not_training_type(self):
        type_not_allowed = (
            MiniTrainingFactory(academic_year=self.academic_year),
            GroupFactory(academic_year=self.academic_year)
        )
        for education_group_year in type_not_allowed:
            with self.subTest(education_group_year=education_group_year):
                perm = CertificateAimsPerms(user=SuperUserFactory(), education_group_year=education_group_year)
                self.assertFalse(perm.is_eligible())

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2020)
    def test_education_group_year_is_lower_than_modification_settings(self):
        super_user = SuperUserFactory()
        perm = CertificateAimsPerms(user=super_user, education_group_year=self.training)
        self.assertFalse(perm.is_eligible())
