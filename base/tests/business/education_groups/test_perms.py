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

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from base.business.education_groups import perms
from base.business.education_groups.perms import is_education_group_edit_period_opened, check_permission, \
    check_authorized_type, is_eligible_to_edit_general_information, is_eligible_to_edit_admission_condition, \
    GeneralInformationPerms, CommonEducationGroupStrategyPerms, AdmissionConditionPerms, \
    _is_eligible_to_add_education_group_with_category
from base.models.enums import academic_calendar_type
from base.models.enums.education_group_categories import TRAINING, Categories
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, \
    EducationGroupYearCommonBachelorFactory, TrainingFactory, MiniTrainingFactory, GroupFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory, CentralManagerFactory, SICFactory, \
    FacultyManagerFactory, UEFacultyManagerFactory, AdministrativeManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


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

    def test_faculty_manager_modify_certificates_aims(self):
        today = datetime.date.today()
        entity_version = EntityVersionFactory()
        entity = entity_version.entity
        person = FacultyManagerFactory()
        PersonEntityFactory(entity=entity, person=person, with_child=True)

        AcademicCalendarFactory(
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )

        test_cases = (
            {'edy': MiniTrainingFactory(academic_year=self.current_academic_year,
                                        management_entity=entity,
                                        administration_entity=entity),
             'person': person,
             'expected_result': False
             },
            {'edy': GroupFactory(academic_year=self.current_academic_year,
                                 management_entity=entity,
                                 administration_entity=entity),
             'person': person,
             'expected_result': False
             },
            {'edy': TrainingFactory(academic_year=self.current_academic_year,
                                    management_entity=entity,
                                    administration_entity=entity),
             'person': person,
             'expected_result': True
             },
        )

        for case in test_cases:
            with self.subTest(msg="{} with raise_exception False".format(case['edy'].education_group_type.category)):
                self.assertEqual(case['expected_result'], perms._is_eligible_certificate_aims(case['person'],
                                                                                              case['edy'],
                                                                                              False))

        for case in test_cases[:-1]:
            with self.subTest(msg="{} with raise_exception True".format(case['edy'].education_group_type.category)):
                self.assertRaises(PermissionDenied,
                                  perms._is_eligible_certificate_aims,
                                  case['person'],
                                  case['edy'],
                                  True)

    def test_is_education_group_edit_period_opened_case_period_closed(self):
        today = datetime.date.today()

        AcademicCalendarFactory(
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertFalse(is_education_group_edit_period_opened(self.education_group_year))

    def test_is_education_group_edit_period_opened_case_period_opened(self):
        today = datetime.date.today()

        AcademicCalendarFactory(
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertTrue(is_education_group_edit_period_opened(self.education_group_year))

    def test_is_education_group_edit_period_opened_case_period_opened_but_not_same_academic_year(self):
        today = datetime.date.today()
        education_group_year = EducationGroupYearFactory(academic_year__year=self.current_academic_year.year + 1)

        AcademicCalendarFactory(
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=self.current_academic_year,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )
        self.assertFalse(is_education_group_edit_period_opened(education_group_year))

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


class TestCommonEducationGroupStrategyPerms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory()
        cls.current_academic_year = create_current_academic_year()
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

    def test_is_current_academic_year_in_range_of_editable_education_group_year_case_not_in_range(self):
        """This test ensure that we cannot modify OF which greater than N+1"""
        training_in_future = TrainingFactory(academic_year__year=self.current_academic_year.year + 2)

        perm = CommonEducationGroupStrategyPerms(self.person.user, training_in_future)
        self.assertFalse(perm._is_current_academic_year_in_range_of_editable_education_group_year())

    def test_is_current_academic_year_in_range_of_editable_education_group_year_case_in_range(self):
        """This test ensure that we modify OF which lower than N+1"""
        training_n1 = TrainingFactory(academic_year__year=self.current_academic_year.year + 1)
        training = TrainingFactory(academic_year=self.current_academic_year)

        for education_group_year in [training_n1, training]:
            perm = CommonEducationGroupStrategyPerms(self.person.user, education_group_year)
            self.assertTrue(perm._is_current_academic_year_in_range_of_editable_education_group_year())

    @mock.patch('base.business.education_groups.perms.check_link_to_management_entity', return_value=True)
    def test_is_linked_to_management_entity(self, mock_check_link):
        training = TrainingFactory()
        perm = CommonEducationGroupStrategyPerms(self.person.user, training)

        self.assertTrue(perm._is_linked_to_management_entity())
        self.assertTrue(mock_check_link.called)

    def test_is_eligible_case_user_as_superuser(self):
        super_user = UserFactory(is_superuser=True)
        training = TrainingFactory()

        perm = CommonEducationGroupStrategyPerms(super_user, training)
        self.assertTrue(perm._is_eligible())

    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_current_academic_year_in_range_of_editable_education_group_year",
        return_value=True)
    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_linked_to_management_entity",
        return_value=True)
    def test_ensure_is_eligible_case_all_submethod_true(self, mock_linked_to_management, mock_is_current_in_range):
        perm = CommonEducationGroupStrategyPerms(self.person.user, TrainingFactory())

        self.assertTrue(perm._is_eligible())
        self.assertTrue(mock_linked_to_management.called)
        self.assertTrue(mock_is_current_in_range.called)

    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_current_academic_year_in_range_of_editable_education_group_year",
        return_value=False)
    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_linked_to_management_entity",
        return_value=True)
    def test_ensure_is_eligible_case_permission_denied(self, mock_linked_to_management, mock_is_current_in_range):
        perm = CommonEducationGroupStrategyPerms(self.person.user, TrainingFactory())

        with self.assertRaises(PermissionDenied):
            perm._is_eligible()

    @mock.patch(
        "base.business.education_groups.perms.CommonEducationGroupStrategyPerms._is_current_academic_year_in_range_of_editable_education_group_year",
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

    def test_is_faculty_manager_case_cannot_modify_data_in_past(self):
        previous_year = self.current_academic_year.year - 1

        training_in_past = TrainingFactory(academic_year__year=previous_year)
        common_in_past = EducationGroupYearCommonBachelorFactory(academic_year__year=previous_year)
        faculty_manager = FacultyManagerFactory()

        for education_group_year in [training_in_past, common_in_past]:
            perm = GeneralInformationPerms(faculty_manager.user, education_group_year)
            with self.assertRaises(PermissionDenied):
                perm._is_faculty_manager_eligible()

    def test_is_faculty_manager_eligible(self):
        faculty_manager = FacultyManagerFactory()

        for education_group_year in [self.training, self.common_bachelor]:
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

    @mock.patch("base.business.education_groups.perms.is_education_group_edit_period_opened", return_value=False)
    def test_is_faculty_manager_case_cannot_modify_data_outside_period(self, mock_calendar_opened):
        person = PersonWithPermissionsFactory()

        perm = AdmissionConditionPerms(person.user, self.training)
        with self.assertRaises(PermissionDenied):
            perm._is_eligible()
