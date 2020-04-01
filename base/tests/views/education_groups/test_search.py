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
import json
import urllib
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.http import HttpResponseForbidden, QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base import utils
from base.forms.education_groups import EducationGroupFilter
from base.models.enums import education_group_categories
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING, GROUP
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_type import EducationGroupTypeFactory, \
    MiniTrainingEducationGroupTypeFactory, \
    GroupEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.user import UserFactory
from base.tests.views.learning_units.search.search_test_mixin import TestRenderToExcelMixin
from base.utils.cache import RequestCache

from waffle.models import Flag
from rest_framework import status

EDUCATION_GROUPS_URL = "education_groups"

FILTER_DATA = {"acronym": ["LBIR"], "title": ["dummy filter"]}
TITLE_EDPH2 = "Edph training 2"
TITLE_EDPH3 = "Edph training 3 [120], sciences"


class TestEducationGroupSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse(EDUCATION_GROUPS_URL)

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
        expected_keys_found = ["form", "object_list", "object_list_count", "enums", "person"]
        self.assertTrue(all(key in response.context.keys() for key in expected_keys_found))

    def test_search_education_group_cache_filter(self):
        self.client.get(self.url, data=FILTER_DATA)
        cached_data = RequestCache(self.user, self.url).cached_data
        self.assertEqual(cached_data, FILTER_DATA)

    def test_flag_version_program_exists(self):
        Flag.objects.create(name='version_program')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_flag_version_program_not_exists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'education_group/search.html')


class TestEducationGroupDataSearchFilter(TestCase):
    """
    In this test class, we will check filter in view which display rigth values
    """
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.previous_academic_year = AcademicYearFactory(year=cls.current_academic_year.year - 1)

        cls.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.type_minitraining = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        cls.type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

        oph_entity = EntityFactory()
        envi_entity = EntityFactory()

        cls.education_group_edph2 = EducationGroupYearFactory(
            acronym='EDPH2', academic_year=cls.current_academic_year,
            partial_acronym='EDPH2_SCS',
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_group,
            management_entity=envi_entity,
            title=TITLE_EDPH2
        )
        cls.education_group_edph3 = EducationGroupYearFactory(
            acronym='EDPH3', academic_year=cls.current_academic_year,
            partial_acronym='EDPH3_SCS',
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=envi_entity,
            title=TITLE_EDPH3
        )

        cls.education_group_arke2a = EducationGroupYearFactory(
            acronym='ARKE2A', academic_year=cls.current_academic_year,
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )

        cls.education_group_hist2a = EducationGroupYearFactory(
            acronym='HIST2A', academic_year=cls.current_academic_year,
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_group,
            management_entity=oph_entity
        )

        cls.education_group_arke2a_previous_year = EducationGroupYearFactory(
            acronym='ARKE2A',
            academic_year=cls.previous_academic_year,
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )

        cls.oph_entity_v = EntityVersionFactory(entity=oph_entity, parent=envi_entity, end_date=None)
        cls.envi_entity_v = EntityVersionFactory(entity=envi_entity, end_date=None)

        cls.user = PersonFactory().user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.form_class = EducationGroupFilter()._meta.form
        cls.url = reverse(EDUCATION_GROUPS_URL)

    def setUp(self):
        self.client.force_login(self.user)
        # Mock cache in order to prevent surprising result
        self.locmem_cache = cache
        self.locmem_cache.clear()
        self.patch = mock.patch.object(utils.cache, 'cache', self.locmem_cache)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_get_request(self):
        response = self.client.get(self.url, data={})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertEqual(context["object_list_count"], 0)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertEqual(context["object_list_count"], 0)

    def test_initial_form_data(self):
        response = self.client.get(self.url)

        form = response.context["form"]
        self.assertEqual(form.fields["academic_year"].initial, self.current_academic_year)
        self.assertEqual(form.fields["category"].initial, education_group_categories.TRAINING)

    def test_with_empty_search_result(self):
        response = self.client.get(self.url, data={"category": education_group_categories.MINI_TRAINING})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertEqual(len(context["object_list"]), 0)
        messages = [str(m) for m in context["messages"]]
        self.assertIn(_('No result!'), messages)

    def test_search_with_acronym_only(self):
        search_strings = [self.education_group_arke2a.acronym,
                          '^{}$'.format(self.education_group_arke2a.acronym),
                          '^{}'.format(self.education_group_arke2a.acronym),
                          '{}$'.format(self.education_group_arke2a.acronym)
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"acronym": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  [self.education_group_arke2a, self.education_group_arke2a_previous_year])

    def test_search_with_acronym_regex(self):
        search_strings = ['^EDPH',
                          'H3$',
                          '^H3$'
                          ]
        result_expected = [
            [self.education_group_edph2, self.education_group_edph3],
            [self.education_group_edph3],
            []
        ]
        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"acronym": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_academic_year_only(self):
        response = self.client.get(self.url, data={"academic_year": self.current_academic_year.id})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_edph2, self.education_group_hist2a,
                               self.education_group_edph3])

    def test_search_with_partial_acronym(self):
        search_strings = [self.education_group_edph2.acronym,
                          '^{}$'.format(self.education_group_edph2.partial_acronym),
                          '^{}'.format(self.education_group_edph2.partial_acronym),
                          '{}$'.format(self.education_group_edph2.partial_acronym),
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"partial_acronym": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"], [self.education_group_edph2])

    def test_search_with_partial_acronym_regex(self):
        search_strings = ['^EDPH',
                          '3_SCS',
                          '^3_SCS']
        result_expected = [
            [self.education_group_edph2, self.education_group_edph3],
            [self.education_group_edph3],
            []
        ]
        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"partial_acronym": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_title(self):
        search_strings = [self.education_group_edph2.title,
                          '^{}$'.format(self.education_group_edph2.title),
                          '^{}'.format(self.education_group_edph2.title),
                          '{}$'.format(self.education_group_edph2.title)
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"title": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"], [self.education_group_edph2])

    def test_search_with_title_regex(self):
        search_strings = ['^Edph training ',
                          ', sciences$',
                          '^ph trai',
                          '120',
                          '[120]'
                          ]
        result_expected = [
            [self.education_group_edph2, self.education_group_edph3],
            [self.education_group_edph3],
            [],
            [self.education_group_edph3],
            [self.education_group_edph3],
        ]

        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"title": search_string})

            self.assertTemplateUsed(response, "education_group/search.html")

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_management_entity(self):
        response = self.client.get(self.url, data={"management_entity": self.oph_entity_v.acronym})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_arke2a_previous_year,
                               self.education_group_hist2a])

    def test_search_with_entities_subordinated(self):
        response = self.client.get(
            self.url,
            data={
                "management_entity": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.education_group_arke2a,
                self.education_group_arke2a_previous_year,
                self.education_group_hist2a,
                self.education_group_edph2,
                self.education_group_edph3
            ]
        )

    def test_search_by_education_group_type(self):
        response = self.client.get(self.url,
                                   data={"education_group_type": self.type_group.id})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"], [self.education_group_hist2a, self.education_group_edph2])

    def test_search_by_education_group_category(self):
        response = self.client.get(self.url,
                                   data={"category": education_group_categories.TRAINING})

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.education_group_arke2a, self.education_group_arke2a_previous_year,
                               self.education_group_edph3])

    def test_with_multiple_criteria(self):
        response = self.client.get(
            self.url, data={
                "academic_year": self.current_academic_year.id,
                "acronym": self.education_group_arke2a.acronym,
                "management_entity": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, "education_group/search.html")

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"], [self.education_group_arke2a])


class TestEducationGroupTypeAutoComplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.trainings = EducationGroupTypeFactory.create_batch(2)
        cls.minitrainings = MiniTrainingEducationGroupTypeFactory.create_batch(3)
        cls.groups = GroupEducationGroupTypeFactory.create_batch(1)

        cls.url = reverse("education_group_type_autocomplete")
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_without_category(self):
        response = self.client.get(self.url)
        json_response = response.json()
        self.assertEqual(6, len(json_response["results"]))

    def test_with_category_set(self):
        tuples_category_woth_expected_result = [(TRAINING, 2), (MINI_TRAINING, 3), (GROUP, 1)]
        for category, expected_result in tuples_category_woth_expected_result:
            with self.subTest(category=category):
                response = self.client.get(self.url, data={"forward": json.dumps({"category": category})})
                json_response = response.json()
                self.assertEqual(expected_result, len(json_response["results"]))

    def test_with_search_query_case_insentive_on_display_value_set(self):
        education_group_type = self.trainings[0]
        search_term = education_group_type.get_name_display().upper()

        response = self.client.get(self.url, data={"forward": json.dumps({"category": TRAINING}), "q": search_term})
        json_response = response.json()

        expected_response = {
            'id': str(education_group_type.pk),
            'selected_text': education_group_type.get_name_display(),
            'text': education_group_type.get_name_display()
        }
        self.assertEqual(len(json_response["results"]), 1)
        self.assertEqual(json_response["results"][0], expected_response)


class TestExcelGeneration(TestRenderToExcelMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce()
        cls.egys = EducationGroupYearFactory.create_batch(4)
        cls.url = reverse(EDUCATION_GROUPS_URL)
        cls.get_data = {
            "academic_year": str(cls.egys[0].academic_year.id),
        }
        cls.tuples_xls_status_value_with_xls_method_function = (
            ("xls", "base.views.education_groups.search.create_xls"),
            ("xls_administrative", "base.views.education_groups.search.create_xls_administrative_data"),
        )

        cls.person = PersonWithPermissionsFactory("can_access_education_group")

    def setUp(self):
        self.client.force_login(self.person.user)
