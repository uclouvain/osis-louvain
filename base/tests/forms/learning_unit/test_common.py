############################################################################
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
############################################################################
import datetime

from django.test import TestCase
from django.urls import reverse

from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_year_subtypes import FULL
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory


class LearningUnitCheckAcronymViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        start_year = AcademicYearFactory(year=today.year+1)
        end_year = AcademicYearFactory(year=today.year+7)
        cls.academic_years = GenerateAcademicYear(start_year=start_year, end_year=end_year)

        cls.a_superuser = SuperUserFactory()
        cls.person = PersonFactory(user=cls.a_superuser)

    def setUp(self):
        self.client.force_login(self.a_superuser)

    def test_learning_unit_check_acronym(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        url = reverse('check_acronym', kwargs={'subtype': FULL})
        get_data = {'acronym': 'goodacronym', 'year_id': self.academic_years[0].id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': False,
             'existing_acronym': False,
             'existed_acronym': False,
             'first_using': "",
             'last_using': ""}
        )

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.academic_years[0]
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.academic_years[0]
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1210', 'year_id': self.academic_years[0].id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': True,
             'existed_acronym': False,
             'first_using': str(self.academic_years[0]),
             'last_using': ""}
        )

        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1211",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.academic_years[0]
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1211', 'year_id': self.academic_years[6].id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': False,
             'existed_acronym': True,
             'first_using': "",
             'last_using': str(self.academic_years[0])}
        )
