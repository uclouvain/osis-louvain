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

from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from base.tests.forms.test_external_learning_unit import get_valid_external_learning_unit_form_data
from base.views.learning_units.external.create import get_external_learning_unit_creation_form
from reference.tests.factories.language import LanguageFactory


@override_flag('learning_unit_external_create', active=True)
class TestCreateExternalLearningUnitView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="add_externallearningunityear"))
        self.person = PersonFactory(user=self.user)
        self.client.force_login(self.user)
        self.academic_year = create_current_academic_year()
        self.language = LanguageFactory(code='FR')
        self.data = get_valid_external_learning_unit_form_data(self.academic_year, self.person)
        self.url = reverse(get_external_learning_unit_creation_form, args=[self.academic_year.pk])

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
