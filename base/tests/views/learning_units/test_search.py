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
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.http.response import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.forms.common import TooManyResultsException
from base.models.enums import learning_container_year_types
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.views.learning_units.search import BORROWED_COURSE, EXTERNAL_SEARCH


class TestSearchBorrowedLearningUnits(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_years = [LearningUnitYearFactory() for _ in range(5)]
        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.url = reverse("learning_units_borrowed_course")
        create_current_academic_year()

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_has_not_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_get_request(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertEqual(context["search_type"], BORROWED_COURSE)
        self.assertTemplateUsed(response, "learning_unit/by_activity.html")


class TestSearchExternalLearningUnits(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_externallearningunityear"))
        cls.url = reverse("learning_units_external")
        create_current_academic_year()

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_has_not_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_get_request(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertEqual(context["search_type"], EXTERNAL_SEARCH)
        self.assertTemplateUsed(response, "learning_unit/by_external.html")


class TestSearchLearningUnitsSimple(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.url = reverse("learning_units")
        cls.academic_year = create_current_academic_year()

    @patch('base.forms.learning_unit.search_form.LearningUnitYearForm.get_activity_learning_units')
    def test_search_too_many_results_displays_warning(self, mock_get_activity_learning_units):
        mock_get_activity_learning_units.side_effect = TooManyResultsException()
        self.client.force_login(self.person.user)

        search_data = {
            "academic_year_id": str(self.academic_year.id),
            "container_type": learning_container_year_types.COURSE
        }
        response = self.client.get(self.url, search_data)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(
            messages[0],
            _('Too many results : Please be more specific on the search criteria.')
        )
