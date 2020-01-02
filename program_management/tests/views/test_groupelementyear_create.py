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

from django.contrib.messages import get_messages
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from base.models.enums.education_group_types import TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, GroupFactory, TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.utils.cache import cache, ElementCache
from program_management.business.group_element_years.management import EDUCATION_GROUP_YEAR


@override_flag('education_group_update', active=True)
class TestAttachCheckView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egy = EducationGroupYearFactory()
        cls.next_academic_year = AcademicYearFactory(current=True)
        cls.group_element_year = GroupElementYearFactory(parent__academic_year=cls.next_academic_year)
        cls.selected_egy = EducationGroupYearFactory(
            academic_year=cls.next_academic_year
        )

        cls.url = reverse("check_education_group_attach", args=[cls.egy.id, cls.egy.id])

        cls.person = PersonFactory()

        cls.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group",
                                      return_value=True)

        cls.attach_strategy_patcher = mock.patch(
            "program_management.views.groupelementyear_create.AttachEducationGroupYearStrategy"
        )

    def setUp(self):
        self.client.force_login(self.person.user)
        self.mocked_perm = self.perm_patcher.start()
        self.mocked_attach_strategy = self.attach_strategy_patcher.start()

    def tearDown(self):
        self.addCleanup(self.perm_patcher.stop)
        self.addCleanup(self.attach_strategy_patcher.stop)
        self.addCleanup(cache.clear)

    def test_when_no_element_selected(self):
        response = self.client.get(self.url)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error_messages": [_("Please cut or copy an item before attach it")]}
        )

    def test_when_all_parameters_not_set(self):
        response = self.client.get(self.url, data={"id": self.egy.id, "content_type": ""})
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error_messages": [_("Please cut or copy an item before attach it")]}
        )

    def test_when_element_selected_and_no_error(self):
        response = self.client.get(self.url, data={"id": self.egy.id, "content_type": EDUCATION_GROUP_YEAR})
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error_messages": []}
        )

        self.assertEqual(
            self.mocked_attach_strategy.call_args_list,
            [
                ({"parent": self.egy, "child": self.egy},)
            ]
        )

    def test_when_multiple_element_selected(self):
        other_egy = EducationGroupYearFactory()
        response = self.client.get(self.url, data={
            "id": [self.egy.id, other_egy.id],
            "content_type": EDUCATION_GROUP_YEAR
        })
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error_messages": []}
        )
        self.assertEqual(
            self.mocked_attach_strategy.call_args_list,
            [
                ({"parent": self.egy, "child": self.egy},),
                ({"parent": self.egy, "child": other_egy},)
            ]
        )


@override_flag('education_group_update', active=True)
class TestCreateGroupElementYearView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egy = TrainingFactory(academic_year__current=True, education_group_type__name=TrainingType.BACHELOR.name)
        cls.next_academic_year = AcademicYearFactory(current=True)
        cls.group_element_year = GroupElementYearFactory(parent__academic_year=cls.next_academic_year)
        cls.selected_egy = EducationGroupYearFactory(
            academic_year=cls.next_academic_year
        )

        cls.url = reverse("group_element_year_create", args=[cls.egy.id, cls.egy.id])

        cls.person = PersonFactory()

        cls.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group",
                                      return_value=True)

        cls.attach_strategy_patcher = mock.patch(
            "program_management.views.groupelementyear_create.AttachEducationGroupYearStrategy"
        )

    def setUp(self):
        self.client.force_login(self.person.user)
        self.mocked_perm = self.perm_patcher.start()
        self.mocked_attach_strategy = self.attach_strategy_patcher.start()

    def tearDown(self):
        self.addCleanup(self.perm_patcher.stop)
        self.addCleanup(self.attach_strategy_patcher.stop)
        self.addCleanup(cache.clear)

    def test_when_no_element_selected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(response.context["education_group_year"], self.egy)

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(msgs, [_("Please cut or copy an item before attach it")])

    def test_when_all_parameters_not_set(self):
        response = self.client.get(
            self.url,
            data={"id": self.egy.id, "content_type": ""},
            follow=True,
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), _("Please cut or copy an item before attach it"))

    def test_when_one_element_selected(self):
        other_egy = GroupFactory(academic_year__current=True, education_group_type__name=GroupType.COMMON_CORE.name)
        AuthorizedRelationshipFactory(
            parent_type=self.egy.education_group_type,
            child_type=other_egy.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        querydict = QueryDict(mutable=True)
        querydict.update({"id": other_egy.id, "content_type": EDUCATION_GROUP_YEAR})
        url_parameters = querydict.urlencode()
        response = self.client.post(self.url + "?" + url_parameters, data={
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
        })

        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

        self.assertTrue(
            GroupElementYear.objects.get(parent=self.egy, child_branch=other_egy)
        )

    def test_when_multiple_elements_selected(self):
        other_egy = GroupFactory(academic_year__current=True)
        other_other_egy = GroupFactory(academic_year__current=True)
        AuthorizedRelationshipFactory(
            parent_type=self.egy.education_group_type,
            child_type=other_egy.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        AuthorizedRelationshipFactory(
            parent_type=self.egy.education_group_type,
            child_type=other_other_egy.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        querydict = QueryDict(mutable=True)
        querydict.update({"content_type": EDUCATION_GROUP_YEAR})
        querydict.setlist("id", [other_egy.id, other_other_egy.id])
        url_parameters = querydict.urlencode()
        response = self.client.post(self.url + "?" + url_parameters, data={
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '2',
        })

        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

        self.assertTrue(
            GroupElementYear.objects.get(parent=self.egy, child_branch=other_egy)
        )
        self.assertTrue(
            GroupElementYear.objects.get(parent=self.egy, child_branch=other_other_egy)
        )


@override_flag('education_group_update', active=True)
class TestMoveGroupElementYearView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.next_academic_year = AcademicYearFactory(current=True)
        cls.root_egy = EducationGroupYearFactory(academic_year=cls.next_academic_year)
        cls.group_element_year = GroupElementYearFactory(parent__academic_year=cls.next_academic_year)
        cls.selected_egy = GroupFactory(
            academic_year=cls.next_academic_year
        )

        cls.url = reverse(
            "group_element_year_move",
            args=[cls.root_egy.id, cls.selected_egy.id, cls.group_element_year.id]
        )

        cls.person = PersonFactory()

        cls.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group",
                                      return_value=True)

    def setUp(self):
        self.client.force_login(self.person.user)
        self.mocked_perm = self.perm_patcher.start()

    def tearDown(self):
        self.addCleanup(self.perm_patcher.stop)
        self.addCleanup(cache.clear)

    def test_move(self):
        AuthorizedRelationshipFactory(
            parent_type=self.selected_egy.education_group_type,
            child_type=self.group_element_year.child_branch.education_group_type,
            min_count_authorized=0,
            max_count_authorized=None
        )
        ElementCache(self.person.user).save_element_selected(
            self.group_element_year.child_branch,
            source_link_id=self.group_element_year.id
        )
        self.client.post(self.url, data={
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '1',
            "link_type": LinkTypes.REFERENCE.name
        })

        self.assertFalse(GroupElementYear.objects.filter(id=self.group_element_year.id))
        self.mocked_perm.assert_any_call(self.person, self.selected_egy, raise_exception=True)
        self.mocked_perm.assert_any_call(self.person, self.group_element_year.parent, raise_exception=True)
