# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.http import HttpResponseForbidden, HttpResponse
from django.test import TestCase
from django.urls import reverse

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearCommonFactory, \
    EducationGroupYearCommonBachelorFactory, EducationGroupYearCommonAgregationFactory, \
    EducationGroupYearCommonMasterFactory, EducationGroupYearCommonSpecializedMasterFactory
from base.tests.factories.person import PersonFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.views.configuration.common_list import CommonListFilterSerializer, CommonListFilter


class TestCommonListFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(number_past=2, number_future=5)

    def test_ensure_academic_year_initial_value_case_no_education_group_switch_calendar_opened(self):
        filter = CommonListFilter()
        self.assertIsNone(filter.form['academic_year'].initial)

    def test_ensure_academic_year_initial_value_case_one_education_group_switch_calendar_opened(self):
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_SWITCH.name,
            data_year=self.academic_years[2]
        )

        filter = CommonListFilter()
        self.assertEqual(filter.form['academic_year'].initial, self.academic_years[2])

    def test_ensure_academic_year_initial_value_case_multiple_education_group_switch_calendar_opened(self):
        for academic_year in self.academic_years[:2]:
            OpenAcademicCalendarFactory(
                reference=AcademicCalendarTypes.EDUCATION_GROUP_SWITCH.name,
                data_year=academic_year
            )

        filter = CommonListFilter()
        self.assertEqual(filter.form['academic_year'].initial, self.academic_years[0])


class TestCommonListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('common_topics_configuration')

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_when_user_has_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_assert_context_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertIn('form', response.context)
        self.assertIn('object_list_count', response.context)
        self.assertIn('items_per_page', response.context)


class TestCommonListFilterSerializer(TestCase):
    def test_assert_main_common_expected_url(self):
        main_common = EducationGroupYearCommonFactory()

        expected_url = reverse('common_general_information', kwargs={'year': main_common.academic_year.year})
        self.assertEqual(
            CommonListFilterSerializer().get_url(main_common),
            expected_url
        )

    def test_assert_bachelor_common_expected_url(self):
        bachelor_common = EducationGroupYearCommonBachelorFactory()

        expected_url = reverse(
            'common_bachelor_admission_condition',
            kwargs={'year': bachelor_common.academic_year.year}
        )
        self.assertEqual(
            CommonListFilterSerializer().get_url(bachelor_common),
            expected_url
        )

    def test_assert_aggregate_common_expected_url(self):
        aggregate_common = EducationGroupYearCommonAgregationFactory()

        expected_url = reverse(
            'common_aggregate_admission_condition',
            kwargs={'year': aggregate_common.academic_year.year}
        )
        self.assertEqual(
            CommonListFilterSerializer().get_url(aggregate_common),
            expected_url
        )

    def test_assert_2m_common_expected_url(self):
        master_2m_common = EducationGroupYearCommonMasterFactory()

        expected_url = reverse(
            'common_master_admission_condition',
            kwargs={'year': master_2m_common.academic_year.year}
        )
        self.assertEqual(
            CommonListFilterSerializer().get_url(master_2m_common),
            expected_url
        )

    def test_assert_mc_common_expected_url(self):
        master_mc_common = EducationGroupYearCommonSpecializedMasterFactory()

        expected_url = reverse(
            'common_master_specialized_admission_condition',
            kwargs={'year': master_mc_common.academic_year.year}
        )
        self.assertEqual(
            CommonListFilterSerializer().get_url(master_mc_common),
            expected_url
        )
