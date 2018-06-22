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
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.http import HttpResponseForbidden

from base.forms.education_group.create import CreateEducationGroupYearForm, CreateOfferYearEntityForm
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory


class TestCreate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent_education_group_year = EducationGroupYearFactory()
        cls.url_without_parent = reverse("new_education_group")
        cls.url_with_parent = reverse("new_education_group", kwargs={"parent_id":cls.parent_education_group_year.id})
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_add_education_group",
                                       side_effect=lambda person: True)
        self.mocked_perm = self.perm_patcher.start()

    def tearDown(self):
        self.perm_patcher.stop()

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url_without_parent)

        self.assertRedirects(response, '/login/?next={}'.format(self.url_without_parent))

    def test_permission_required(self):
        response = self.client.get(self.url_without_parent)

        self.mocked_perm.assert_called_once_with(self.person)


    def test_template_used(self):
        response = self.client.get(self.url_without_parent)

        self.assertTemplateUsed(response, "education_group/creation.html")

    def test_with_parent_set(self):
        response = self.client.get(self.url_without_parent)

        self.assertTemplateUsed(response, "education_group/creation.html")

    def test_response_context(self):
        response = self.client.get(self.url_without_parent)

        form_education_group_year = response.context["form_education_group_year"]
        form_offer_year_entity  =  response.context["form_offer_year_entity"]

        self.assertIsInstance(form_education_group_year, CreateEducationGroupYearForm)
        self.assertIsInstance(form_offer_year_entity, CreateOfferYearEntityForm)
