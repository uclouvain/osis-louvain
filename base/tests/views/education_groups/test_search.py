##############################################################################
#
#    OSIS stands for Open Student Information System. It"s an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base import utils
from base.forms.education_groups import EducationGroupFilter
from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory

FILTER_DATA = {"acronym": "LBIR", "title": "dummy filter"}


class TestEducationGroupSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_groups")

    def setUp(self):
        self.client.force_login(self.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_search_education_group_using_template_use(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/search.html")

    def test_search_education_group_keys_exists_in_context(self):
        response = self.client.get(self.url)
        expected_keys_found = ["form", "object_list", "object_list_count", "experimental_phase", "enums", "person"]
        self.assertTrue(all(key in response.context.keys() for key in expected_keys_found))

    @mock.patch("base.utils.cache._save_filter_to_cache", side_effect=lambda *args,**kwargs: True)
    def test_search_education_group_cache_filter(self, mock_save_filter_to_cache):
        response = self.client.get(self.url, data=FILTER_DATA)
        self.assertTrue(mock_save_filter_to_cache.called)

        # Ensure that we don't cache field related to xls
        mock_save_filter_to_cache.assert_called_once_with(response.wsgi_request,
                                                          exclude_params=['xls_status', 'xls_order_col'])


class TestEducationGroupDataSearchFilter(TestCase):
    """
    In this test class, we will check filter in view which display rigth values
    """
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        cls.academic_year = AcademicYearFactory(start_date=today, end_date=today.replace(year=today.year + 1),
                                                year=today.year)
        cls.previous_academic_year = AcademicYearFactory(start_date=today.replace(year=today.year - 1),
                                                         end_date=today - datetime.timedelta(days=1),
                                                         year=today.year - 1)

        cls.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.type_minitraining = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        cls.type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

        oph_entity = EntityFactory()
        envi_entity = EntityFactory()

        cls.education_group_edph2 = EducationGroupYearFactory(
            acronym='EDPH2', academic_year=cls.academic_year,
            partial_acronym='EDPH2_SCS',
            education_group_type=cls.type_group,
            management_entity=envi_entity
        )

        cls.education_group_arke2a = EducationGroupYearFactory(
            acronym='ARKE2A', academic_year=cls.academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )

        cls.education_group_hist2a = EducationGroupYearFactory(
            acronym='HIST2A', academic_year=cls.academic_year,
            education_group_type=cls.type_group,
            management_entity=oph_entity
        )

        cls.education_group_arke2a_previous_year = EducationGroupYearFactory(
            acronym='ARKE2A',
            academic_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )

        cls.oph_entity_v = EntityVersionFactory(entity=oph_entity, parent=envi_entity, end_date=None)
        cls.envi_entity_v = EntityVersionFactory(entity=envi_entity, end_date=None)

        cls.user = PersonFactory().user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_groups")

    def setUp(self):
        self.client.force_login(self.user)
        # Mock cache in order to prevent surprising result
        self.locmem_cache = cache
        self.locmem_cache.clear()
        self.patch = mock.patch.object(utils.cache, 'cache', self.locmem_cache)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_post_request(self):
        response = self.client.post(self.url, data={})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["object_list_count"], 0)
        self.assertEqual(context["experimental_phase"], True)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["object_list_count"], 0)
        self.assertEqual(context["experimental_phase"], True)

    def test_initial_form_data(self):
        response = self.client.get(self.url)

        form = response.context["form"]
        self.assertEqual(form.initial["academic_year"], self.academic_year)
        self.assertEqual(form.initial["category"], education_group_categories.TRAINING)

    def test_with_empty_search_result(self):
        response = self.client.get(self.url, data={"category": education_group_categories.MINI_TRAINING})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertEqual(len(context["object_list"]), 0)
        messages = [str(m) for m in context["messages"]]
        self.assertIn(_('No result!'), messages)

    def test_search_with_acronym_only(self):
        response = self.client.get(self.url, data={"acronym": self.education_group_arke2a.acronym})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_arke2a_previous_year])

    def test_search_with_academic_year_only(self):
        response = self.client.get(self.url, data={"academic_year": self.academic_year.id})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_edph2, self.education_group_hist2a])

    def test_search_with_partial_acronym(self):
        response = self.client.get(self.url, data={"partial_acronym": self.education_group_edph2.partial_acronym})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"], [self.education_group_edph2])

    def test_search_with_requirement_entity(self):
        response = self.client.get(self.url,
                                   data={"requirement_entity_acronym": self.oph_entity_v.acronym})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_arke2a_previous_year,
                               self.education_group_hist2a])

    def test_search_with_entities_subordinated(self):
        response = self.client.get(
            self.url,
            data={
                "requirement_entity_acronym": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(
            context["object_list"],
            [
                self.education_group_arke2a,
                self.education_group_arke2a_previous_year,
                self.education_group_hist2a,
                self.education_group_edph2
            ]
        )

    def test_search_by_education_group_type(self):
        response = self.client.get(self.url,
                                   data={"education_group_type": self.type_group.id})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"], [self.education_group_hist2a, self.education_group_edph2])

    def test_search_by_education_group_category(self):
        response = self.client.get(self.url,
                                   data={"category": education_group_categories.TRAINING})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_arke2a_previous_year])

    def test_with_multiple_criteria(self):
        response = self.client.get(
            self.url, data={
                "academic_year": self.academic_year.id,
                "acronym": self.education_group_arke2a.acronym,
                "requirement_entity_acronym": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], EducationGroupFilter)
        self.assertEqual(context["experimental_phase"], True)
        self.assertCountEqual(context["object_list"], [self.education_group_arke2a])
