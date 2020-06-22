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
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages, SUCCESS
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from base.tests.forms.test_external_learning_unit import get_valid_external_learning_unit_form_data
from base.views.learning_units.external.create import get_external_learning_unit_creation_form
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory

YEAR_LIMIT_LUE_MODIFICATION = 2018


@override_flag('learning_unit_external_create', active=True)
class TestCreateExternalLearningUnitView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonWithPermissionsFactory(
            'can_access_learningunit', 'can_create_learningunit', 'add_externallearningunityear',
            user=cls.user
        )

        starting_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION)
        end_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION + 1)
        cls.academic_years = GenerateAcademicYear(starting_year, end_year).academic_years
        cls.academic_year = cls.academic_years[1]
        cls.language = FrenchLanguageFactory()
        cls.data = get_valid_external_learning_unit_form_data(cls.academic_year, cls.person)
        cls.url = reverse(get_external_learning_unit_creation_form, args=[cls.academic_year.pk])

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_get_permission_denied(self):
        self.user.user_permissions.remove(Permission.objects.get(codename="add_externallearningunityear"))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_post(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        messages = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages, [SUCCESS])
