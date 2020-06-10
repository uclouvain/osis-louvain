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
from datetime import datetime
from unittest import mock

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.forms.education_group.group import GroupYearModelForm
from base.forms.education_group.mini_training import MiniTrainingYearModelForm
from base.forms.education_group.training import TrainingEducationGroupYearForm
from base.models.enums import education_group_categories, organization_type, internship_presence
from base.models.enums.active_status import ACTIVE
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.entity_type import FACULTY
from base.models.enums.schedule_type import DAILY
from base.models.exceptions import ValidationWarning
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.views.education_groups.create import PERMS_BY_CATEGORY
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from reference.tests.factories.language import LanguageFactory


class TestCreateMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        start_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        end_year = AcademicYearFactory(year=cls.current_academic_year.year + 10)
        cls.generated_ac_years = GenerateAcademicYear(start_year, end_year)
        cls.parent_education_group_year = EducationGroupYearFactory(academic_year=cls.current_academic_year)

        cls.test_categories = [
            education_group_categories.GROUP,
            education_group_categories.TRAINING,
            education_group_categories.MINI_TRAINING,
        ]

        cls.education_group_types = [
            EducationGroupTypeFactory(category=category)
            for category in cls.test_categories
        ]
        cls.organization = OrganizationFactory(type=organization_type.MAIN)
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(entity=cls.entity, entity_type=FACULTY, start_date=datetime.now())
        cls.language = LanguageFactory()
        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.entity)


@override_flag('education_group_create', active=True)
class TestCreate(TestCreateMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.urls_without_parent_by_category = {
            education_group_type.category:
                reverse(
                    "new_education_group",
                    kwargs={
                        "category": education_group_type.category,
                        "education_group_type_pk": education_group_type.pk,
                    }
                )
            for education_group_type in cls.education_group_types
        }
        cls.urls_with_parent_by_category = {
            education_group_type.category:
                reverse(
                    "new_education_group",
                    kwargs={
                        "category": education_group_type.category,
                        "education_group_type_pk": education_group_type.pk,
                        "root_id": cls.parent_education_group_year.id,
                        "parent_id": cls.parent_education_group_year.id,
                    }
                )
            for education_group_type in cls.education_group_types
        }

        cls.expected_templates_by_category = {
            education_group_categories.GROUP: "education_group/create_groups.html",
            education_group_categories.TRAINING: "education_group/create_trainings.html",
            education_group_categories.MINI_TRAINING: "education_group/create_mini_trainings.html",
        }

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_login_required(self):
        self.client.logout()
        for url in self.urls_without_parent_by_category.values():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, '/login/?next={}'.format(url))

    def test_permission_required_case_user_have_perms(self):
        for category, url in self.urls_without_parent_by_category.items():
            with self.subTest(url=url):
                self.client.get(url)
                self.mocked_perm.assert_any_call(PERMS_BY_CATEGORY[category], None)

    def test_template_used(self):
        for category in self.test_categories:
            with self.subTest(category=category):
                response = self.client.get(self.urls_without_parent_by_category.get(category))
                self.assertTemplateUsed(response, self.expected_templates_by_category.get(category))

    def test_with_parent_set(self):
        for egt in self.education_group_types:
            AuthorizedRelationshipFactory(
                child_type=egt,
                parent_type=self.parent_education_group_year.education_group_type
            )

        for category in self.test_categories:
            with self.subTest(category=category):
                response = self.client.get(self.urls_with_parent_by_category.get(category))
                self.assertTemplateUsed(response, self.expected_templates_by_category.get(category))

    def test_response_context_for_group(self):
        url = self.urls_without_parent_by_category[education_group_categories.GROUP]
        response = self.client.get(url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertIsInstance(
            response.context["form_education_group_year"],
            GroupYearModelForm
        )
        self.assertFalse("show_diploma_tab" in response.context)

    def test_response_context_for_training(self):
        url = self.urls_without_parent_by_category[education_group_categories.TRAINING]
        response = self.client.get(url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertIsInstance(
            response.context["form_education_group_year"],
            TrainingEducationGroupYearForm
        )
        self.assertTrue(response.context["show_diploma_tab"])

    def test_response_context_for_mini_training(self):
        url = self.urls_without_parent_by_category[education_group_categories.MINI_TRAINING]
        response = self.client.get(url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertIsInstance(
            response.context["form_education_group_year"],
            MiniTrainingYearModelForm
        )
        self.assertFalse("show_diploma_tab" in response.context)


@override_flag('education_group_create', active=True)
class TestCreateForm(TestCreateMixin):
    def setUp(self):
        self.client.force_login(self.person.user)

    def test_redirect_after_creation(self):
        url = reverse('new_education_group', args=[self.education_group_types[1].category,
                                                   self.education_group_types[1].id])
        data = {
            'acronym': 'YOLO1BA',
            'partial_acronym': 'LYOLO1B',
            'active': 'ACTIVE',
            'schedule_type': 'DAILY',
            'credits': '180',
            'title': 'Bachelier en',
            'academic_year': self.current_academic_year.id,
            'management_entity': self.entity_version.id,
            'administration_entity': self.entity_version.id,
            'internship': ['NO'],
            'primary_language': self.language.id,
            'diploma_printing_title': "title",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_redirect_after_creation_failed(self):
        url = reverse('new_education_group', args=[self.education_group_types[1].category,
                                                   self.education_group_types[1].id])
        data = {
            'acronym': 'YOLO1BA',
            'active': ACTIVE,
            'schedule_type': DAILY,
            'title': 'Bachelier en',
            'academic_year': self.current_academic_year.id,
            'management_entity': self.entity_version.id,
            'administration_entity': self.entity_version.id,
            'internship': internship_presence.NO,
            'primary_language': self.language.id,
            'diploma_printing_title': "title",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(url, response.request['PATH_INFO'])


class TestValidateField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.person = PersonFactory()
        cls.url = reverse('validate_education_group_field', args=[TRAINING])

    def setUp(self):
        self.client.force_login(self.person.user)

        mock_clean_acronym = mock.patch(
            "base.models.education_group_year.EducationGroupYear.clean_acronym",
            return_value=None
        )
        self.mocked_clean_acronym = mock_clean_acronym.start()
        self.addCleanup(mock_clean_acronym.stop)

        mock_clean_partial_acronym = mock.patch(
            "base.models.education_group_year.EducationGroupYear.clean_partial_acronym",
            return_value=None
        )
        self.mocked_clean_partial_acronym = mock_clean_partial_acronym.start()
        self.addCleanup(mock_clean_partial_acronym.stop)

    def test_response_should_be_empty_when_fields_are_valid(self):
        response = self.client.get(
            self.url,
            data={"academic_year": self.academic_year.pk, "acronym": "TEST"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {}
        )

    def test_response_should_contain_error_message_when_field_not_valid(self):
        self.mocked_clean_acronym.side_effect = ValidationError({"acronym": "error acronym"})
        self.mocked_clean_partial_acronym.side_effect = ValidationWarning({"partial_acronym": "error partial"})

        response = self.client.get(
            self.url,
            data={"academic_year": self.academic_year.pk, "acronym": "TEST"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"acronym": {"msg": "error acronym", "level": messages.DEFAULT_TAGS[messages.ERROR]},
             "partial_acronym": {"msg": "error partial", "level": messages.DEFAULT_TAGS[messages.WARNING]}}
        )
