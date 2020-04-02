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
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base import utils
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
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from base.utils.cache import RequestCache
from education_group.tests.factories.group import GroupFactory as EducationGroupGroupFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.forms.education_groups import GroupFilter, STANDARD, PARTICULAR
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory, \
    StandardTransitionEducationGroupVersionFactory, ParticularTransitionEducationGroupVersionFactory

URL_EDUCATION_GROUPS = "version_program"
SEARCH_TEMPLATE = "search.html"

FILTER_DATA = {"acronym": ["LBIR"], "title": ["dummy filter"]}
TITLE_EDPH2 = "Edph training 2"
TITLE_EDPH3 = "Edph training 3 [120], sciences"


class TestEducationGroupSearchView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse(URL_EDUCATION_GROUPS)

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
        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

    def test_search_education_group_keys_exists_in_context(self):
        response = self.client.get(self.url)
        expected_keys_found = ["form", "object_list", "object_list_count", "enums", "person"]
        self.assertTrue(all(key in response.context.keys() for key in expected_keys_found))

    def test_search_education_group_cache_filter(self):
        self.client.get(self.url, data=FILTER_DATA)
        cached_data = RequestCache(self.user, self.url).cached_data
        self.assertEqual(cached_data, FILTER_DATA)


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
        cls.group_year_edph2 = GroupYearFactory(
            acronym='EDPH2', academic_year=cls.current_academic_year,
            partial_acronym='EDPH2_SCS',
            education_group_type=cls.type_group,
            management_entity=envi_entity,
            title_fr=TITLE_EDPH2,
            group__start_year=cls.current_academic_year
        )
        cls.education_group_edph3 = EducationGroupYearFactory(
            acronym='EDPH3', academic_year=cls.current_academic_year,
            partial_acronym='EDPH3_SCS',
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=envi_entity,
            title=TITLE_EDPH3
        )
        cls.group_year_edph3 = GroupYearFactory(
            acronym='EDPH3',
            academic_year=cls.current_academic_year,
            partial_acronym='EDPH3_SCS',
            education_group_type=cls.type_training,
            management_entity=envi_entity,
            title_fr=TITLE_EDPH3,
            group__start_year=cls.current_academic_year
        )
        cls.education_group_arke2a = EducationGroupYearFactory(
            acronym='ARKE2A', academic_year=cls.current_academic_year,
            education_group__start_year=cls.current_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )
        cls.group_year_arke2a = GroupYearFactory(
            acronym='ARKE2A', academic_year=cls.current_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity,
            group__start_year=cls.current_academic_year
        )

        cls.education_group_hist2a = EducationGroupYearFactory(
            acronym='HIST2A', academic_year=cls.current_academic_year,
            education_group__start_year=cls.previous_academic_year,
            education_group_type=cls.type_group,
            management_entity=oph_entity
        )
        cls.group_year_hist2a = GroupYearFactory(
            acronym='HIST2A', academic_year=cls.current_academic_year,
            education_group_type=cls.type_group,
            management_entity=oph_entity,
            group__start_year=cls.current_academic_year
        )

        cls.education_group_arke2a_previous_year = EducationGroupYearFactory(
            acronym='ARKE2A',
            academic_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity
        )
        cls.group_year_arke2a_previous_year = GroupYearFactory(
            acronym='ARKE2A',
            academic_year=cls.previous_academic_year,
            education_group_type=cls.type_training,
            management_entity=oph_entity,
            group__start_year=cls.previous_academic_year
        )

        cls.oph_entity_v = EntityVersionFactory(entity=oph_entity, parent=envi_entity, end_date=None)
        cls.envi_entity_v = EntityVersionFactory(entity=envi_entity, end_date=None)

        cls.user = PersonFactory().user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.form_class = GroupFilter()._meta.form
        cls.url = reverse(URL_EDUCATION_GROUPS)

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

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertEqual(context["object_list_count"], 0)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

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

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertEqual(len(context["object_list"]), 0)
        messages = [str(m) for m in context["messages"]]
        self.assertIn(_('No result!'), messages)

    def test_search_with_acronym_only(self):
        search_strings = [self.group_year_arke2a.acronym,
                          '^{}$'.format(self.group_year_arke2a.acronym),
                          '^{}'.format(self.group_year_arke2a.acronym),
                          '{}$'.format(self.group_year_arke2a.acronym)
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"acronym": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  [self.group_year_arke2a, self.group_year_arke2a_previous_year])

    def test_search_with_acronym_regex(self):
        search_strings = ['^EDPH',
                          'H3$',
                          '^H3$'
                          ]
        result_expected = [
            [self.group_year_edph2, self.group_year_edph3],
            [self.group_year_edph3],
            []
        ]
        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"acronym": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_academic_year_only(self):
        response = self.client.get(self.url, data={"academic_year": self.current_academic_year.id})

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.group_year_arke2a, self.group_year_edph2, self.group_year_hist2a,
                               self.group_year_edph3])

    def test_search_with_partial_acronym(self):
        search_strings = [self.education_group_edph2.acronym,
                          '^{}$'.format(self.education_group_edph2.partial_acronym),
                          '^{}'.format(self.education_group_edph2.partial_acronym),
                          '{}$'.format(self.education_group_edph2.partial_acronym),
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"partial_acronym": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"], [self.group_year_edph2])

    def test_search_with_partial_acronym_regex(self):
        search_strings = ['^EDPH',
                          '3_SCS',
                          '^3_SCS']
        result_expected = [
            [self.group_year_edph2, self.group_year_edph3],
            [self.group_year_edph3],
            []
        ]
        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"partial_acronym": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_title(self):
        search_strings = [self.group_year_edph2.title_fr,
                          '^{}$'.format(self.group_year_edph2.title_fr),
                          '^{}'.format(self.group_year_edph2.title_fr),
                          '{}$'.format(self.group_year_edph2.title_fr)
                          ]
        for search_string in search_strings:
            response = self.client.get(self.url, data={"title_fr": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"], [self.group_year_edph2])

    def test_search_with_title_regex(self):
        search_strings = ['^Edph training ',
                          ', sciences$',
                          '^ph trai',
                          '120',
                          '[120]'
                          ]
        result_expected = [
            [self.group_year_edph2, self.group_year_edph3],
            [self.group_year_edph3],
            [],
            [self.group_year_edph3],
            [self.group_year_edph3],
        ]

        for idx, search_string in enumerate(search_strings):
            response = self.client.get(self.url, data={"title_fr": search_string})

            self.assertTemplateUsed(response, SEARCH_TEMPLATE)

            context = response.context
            self.assertIsInstance(context["form"], self.form_class)
            self.assertCountEqual(context["object_list"],
                                  result_expected[idx])

    def test_search_with_management_entity(self):
        response = self.client.get(self.url, data={"management_entity": self.oph_entity_v.acronym})

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.group_year_arke2a, self.group_year_arke2a_previous_year,
                               self.group_year_hist2a])

    def test_search_with_entities_subordinated(self):
        response = self.client.get(
            self.url,
            data={
                "management_entity": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.group_year_arke2a,
                self.group_year_hist2a,
                self.group_year_edph2,
                self.group_year_edph3,
                self.group_year_arke2a_previous_year
            ]
        )

    def test_search_by_education_group_type(self):
        response = self.client.get(self.url,
                                   data={"education_group_type": self.type_group.id})

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"], [self.group_year_hist2a, self.group_year_edph2])

    def test_search_by_education_group_category(self):
        response = self.client.get(self.url,
                                   data={"category": education_group_categories.TRAINING})

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"],
                              [self.group_year_arke2a,
                               self.group_year_edph3,
                               self.group_year_arke2a_previous_year])

    def test_with_multiple_criteria(self):
        response = self.client.get(
            self.url, data={
                "academic_year": self.current_academic_year.id,
                "acronym": self.education_group_arke2a.acronym,
                "management_entity": self.envi_entity_v.acronym,
                "with_entity_subordinated": True
            }
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(context["object_list"], [self.group_year_arke2a])


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


class TestEducationGroupDataSearchFilterWithVersion(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.previous_academic_year = AcademicYearFactory(year=cls.current_academic_year.year - 1)
        group = EducationGroupGroupFactory(start_year=cls.current_academic_year)
        cls.standard_group_yr = GroupYearFactory(group=group, academic_year=cls.current_academic_year)
        cls.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)

        cls.egy = EducationGroupYearFactory(
            academic_year=cls.current_academic_year,
            education_group_type=cls.type_training,
            acronym="CRIM2M",
            education_group__start_year=cls.current_academic_year,
        )
        cls.root_egv = EducationGroupVersionFactory(root_group=cls.standard_group_yr, offer=cls.egy, version_name='')

        group_transition = EducationGroupGroupFactory(start_year=cls.current_academic_year)
        cls.transition_group_yr = GroupYearFactory(group=group_transition, academic_year=cls.current_academic_year)
        cls.transition_egv = StandardTransitionEducationGroupVersionFactory(
            root_group=cls.transition_group_yr, offer=cls.egy)

        cls.particular_group_yr_1 = GroupYearFactory(group=group_transition,
                                                     academic_year=cls.current_academic_year)
        cls.particular_egv_1 = EducationGroupVersionFactory(root_group=cls.particular_group_yr_1,
                                                            offer=cls.egy,
                                                            version_name='CMES-1',
                                                            is_transition=False)

        cls.particular_group_yr_2 = GroupYearFactory(group=group_transition,
                                                     academic_year=cls.current_academic_year)
        cls.particular_egv_2 = EducationGroupVersionFactory(root_group=cls.particular_group_yr_2,
                                                            offer=cls.egy, version_name='CMES-2',
                                                            is_transition=False)

        # Transition of particular
        group_transition_particular_group_yr_2 = EducationGroupGroupFactory(start_year=cls.current_academic_year)
        cls.transition_group_yr_2_transition = GroupYearFactory(group=group_transition_particular_group_yr_2,
                                                                academic_year=cls.current_academic_year)
        cls.transition_egv = ParticularTransitionEducationGroupVersionFactory(
            root_group=cls.transition_group_yr_2_transition,
            offer=cls.egy)
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse(URL_EDUCATION_GROUPS)
        cls.form_class = GroupFilter()._meta.form

    def setUp(self):
        self.client.force_login(self.user)

    def test_with_entity_transition(self):

        response = self.client.get(
            self.url,
            data={'with_entity_transition': True}  # Default value
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.standard_group_yr,
                self.transition_group_yr,
                self.particular_group_yr_1,
                self.particular_group_yr_2,
                self.transition_group_yr_2_transition
            ]
        )

    def test_with_version_standard(self):

        response = self.client.get(
            self.url,
            data={'with_entity_transition': True,
                  'version': STANDARD}
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.standard_group_yr,
                self.transition_group_yr
            ]
        )

    def test_with_version_standard_with_entity_transition_is_false(self):
        response = self.client.get(
            self.url,
            data={'version': STANDARD}  # Default value
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.standard_group_yr
            ]
        )

    def test_with_version_particular(self):
        response = self.client.get(
            self.url,
            data={'with_entity_transition': True,
                  'version': PARTICULAR}
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.particular_group_yr_1,
                self.particular_group_yr_2,
                self.transition_group_yr_2_transition
            ]
        )

    def test_with_version_particular_with_entity_transition_is_false(self):
        response = self.client.get(
            self.url,
            data={'version': PARTICULAR}
        )

        self.assertTemplateUsed(response, SEARCH_TEMPLATE)

        context = response.context
        self.assertIsInstance(context["form"], self.form_class)
        self.assertCountEqual(
            context["object_list"],
            [
                self.particular_group_yr_1,
                self.particular_group_yr_2
            ]
        )
