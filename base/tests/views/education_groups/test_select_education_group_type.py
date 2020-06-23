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
from unittest import mock

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory


@override_flag('education_group_create', active=True)
class TestSelectEducationGroupTypeView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        create_current_academic_year()
        cls.parent_education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)

        cls.test_categories = [
            education_group_categories.GROUP,
            education_group_categories.TRAINING,
            education_group_categories.MINI_TRAINING,
        ]

        cls.education_group_types = [
            EducationGroupTypeFactory(category=category)
            for category in cls.test_categories
        ]

        cls.auth_rels = [
            AuthorizedRelationshipFactory(
                parent_type=cls.parent_education_group_year.education_group_type,
                child_type=eg_type,
                min_count_authorized=0,
                max_count_authorized=1,
            )
            for eg_type in cls.education_group_types
        ]

        cls.person = PersonFactory()

    def setUp(self):
        self.perm_patcher = mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

        self.client.force_login(self.person.user)

    def test_get(self):
        response = self.client.get(
            reverse(
                "select_education_group_type",
                args=[self.test_categories[0]]
            )
        )
        self.assertTemplateUsed(response, "education_group/blocks/form/education_group_type.html")

    def test_post_when_no_parent(self):
        response = self.client.post(
            reverse(
                "select_education_group_type",
                args=[self.test_categories[0]]
            ), data={"name": self.education_group_types[0].pk}
        )

        self.assertRedirects(
            response,
            reverse(
                "new_education_group",
                args=[self.test_categories[0], self.education_group_types[0].pk]
            )
        )

    def test_post(self):
        response = self.client.post(
            reverse(
                "select_education_group_type",
                args=[self.test_categories[0], self.parent_education_group_year.pk, self.parent_education_group_year.pk]
            ), data={"name": self.education_group_types[0].pk}
        )

        self.assertRedirects(
            response,
            reverse(
                "new_education_group",
                args=[self.test_categories[0], self.education_group_types[0].pk, self.parent_education_group_year.pk,
                      self.parent_education_group_year.pk]
            )
        )

    def test_post_invalid_when_max_limit_reached(self):
        GroupElementYearFactory(
            parent=self.parent_education_group_year,
            child_branch__academic_year=self.academic_year,
            child_branch__education_group_type=self.education_group_types[0]
        )
        expected_error_msg = _("The number of children of type \"%(child_type)s\" for \"%(parent)s\" "
                               "has already reached the limit.") % {
            'child_type': self.education_group_types[0],
            'parent': self.parent_education_group_year
        }
        response = self.client.post(
            reverse(
                "select_education_group_type",
                args=[self.test_categories[0], self.parent_education_group_year.pk, self.parent_education_group_year.pk]
            ), data={"name": self.education_group_types[0].pk}
        )
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertDictEqual(
            response.context["form"].errors,
            {"name": [expected_error_msg]}
        )

    def test_post_invalid(self):
        response = self.client.post(
            reverse(
                "select_education_group_type",
                args=[self.test_categories[0]]
            ), data={"name": self.education_group_types[1].pk}
        )
        self.assertEqual(len(response.context["form"].errors), 1)
