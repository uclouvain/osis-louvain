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
from http import HTTPStatus
from unittest import mock

from django.http import HttpResponseForbidden, QueryDict
from django.test import TestCase
from django.urls import reverse

from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.enums import organization_type
from base.models.enums.education_group_types import TrainingType
from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_year import TrainingFactory, EducationGroupYearCommonFactory, \
    EducationGroupYearMasterFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory

DELETE_URL_NAME = "publication_contact_delete"
EDIT_URL_NAME = "publication_contact_edit"
EDIT_ENTITY_URL_NAME = 'publication_contact_entity_edit'
CREATE_URL_NAME = "publication_contact_create"


class PublicationContactViewSetupTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Common offer must exist
        cls.academic_year = create_current_academic_year()
        EducationGroupYearCommonFactory(academic_year=cls.academic_year)

        cls.training = EducationGroupYearMasterFactory(
            academic_year=cls.academic_year,
        )
        cls.publication_contact = EducationGroupPublicationContactFactory(
            education_group_year=cls.training,
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name
        )

        # Create a central manager and linked it to entity of training
        cls.person = CentralManagerFactory("change_educationgroup", "can_access_education_group")
        PersonEntityFactory(person=cls.person, entity=cls.training.management_entity)

    def setUp(self):
        self.client.force_login(self.person.user)


class TestPublicationContactCreateView(PublicationContactViewSetupTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_create = reverse(
            CREATE_URL_NAME,
            args=[
                cls.training.pk,
                cls.training.pk,
            ]
        )

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url_create)
        self.assertRedirects(response, "/login/?next={}".format(self.url_create))

    def test_user_without_permission(self):
        # Remove permission
        self.person.user.user_permissions.clear()

        response = self.client.get(self.url_create)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_assert_template_used(self, mock_permissions):
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/blocks/modal/modal_publication_contact_edit_inner.html")

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_create_post(self, mock_permissions):
        # Remove current
        self.publication_contact.delete()

        data = {
            "type": PublicationContactType.JURY_MEMBER.name,
            "email": "person@gmail.com",
            "role_fr": "dummy role in french",
            "role_en": "dummy role in english"
        }
        response = self.client.post(self.url_create, data=data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Check into database for created value
        EducationGroupPublicationContact.objects.get(
            education_group_year_id=self.training.id,
            type=data['type'],
            email=data['email'],
            role_fr=data['role_fr'],
            role_en=data['role_en'],
        )


class TestPublicationContactUpdateView(PublicationContactViewSetupTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_edit = reverse(
            EDIT_URL_NAME,
            args=[
                cls.training.pk,
                cls.training.pk,
                cls.publication_contact.pk
            ]
        )

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url_edit)
        self.assertRedirects(response, "/login/?next={}".format(self.url_edit))

    def test_user_without_permission(self):
        # Remove permission
        self.person.user.user_permissions.clear()

        response = self.client.get(self.url_edit)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_assert_template_used(self, mock_permissions):
        response = self.client.get(self.url_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/blocks/modal/modal_publication_contact_edit_inner.html")


class TestPublicationContactDeleteView(PublicationContactViewSetupTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_delete = reverse(
            DELETE_URL_NAME,
            args=[
                cls.training.id,
                cls.training.id,
                cls.publication_contact.pk
            ]
        )

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url_delete)
        self.assertRedirects(response, "/login/?next={}".format(self.url_delete))

    def test_user_without_permission(self):
        # Remove permission
        self.person.user.user_permissions.clear()

        response = self.client.get(self.url_delete)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_template_used(self, mock_permission):
        response = self.client.get(self.url_delete)
        self.assertTemplateUsed(
            response,
            "education_group/blocks/modal/modal_publication_contact_confirm_delete_inner.html",
        )

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_delete_assert_redirection(self, mock_permissions):
        query_dictionary = QueryDict('', mutable=True)
        query_dictionary.update(
            {
                'anchor': True
            }
        )
        http_referer = reverse('education_group_general_informations', args=[
            self.training.pk,
            self.training.pk,
        ])
        response_expected = '{base_url}?{querystring}'.format(
            base_url=http_referer,
            querystring=query_dictionary.urlencode()
        )
        response = self.client.post(self.url_delete, follow=True)
        self.assertRedirects(response, response_expected)
        with self.assertRaises(EducationGroupPublicationContact.DoesNotExist):
            self.publication_contact.refresh_from_db()


class TestEntityPublicationContactUpdateView(PublicationContactViewSetupTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.entity = EntityFactory(organization__type=organization_type.MAIN)
        today = datetime.date.today()
        cls.entity_version = EntityVersionFactory(
            start_date=today.replace(year=1900),
            end_date=None,
            entity=cls.entity,
        )

        cls.url_update = reverse(
            EDIT_ENTITY_URL_NAME,
            args=[
                cls.training.id,
                cls.training.id,
            ]
        )

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url_update)
        self.assertRedirects(response, "/login/?next={}".format(self.url_update))

    def test_user_without_permission(self):
        # Remove permission
        self.person.user.user_permissions.clear()

        response = self.client.get(self.url_update)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_template_used(self, mock_permission):
        response = self.client.get(self.url_update)
        self.assertTemplateUsed(
            response,
            "education_group/blocks/modal/modal_publication_contact_entity_edit_inner.html",
        )

    @mock.patch("base.business.education_groups.perms.GeneralInformationPerms.is_eligible", return_value=True)
    def test_update_assert_db(self, mock_permission):
        response = self.client.post(self.url_update, {
            'publication_contact_entity': self.entity_version.pk
        }, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Check into database for created value
        self.training.refresh_from_db()
        self.assertEqual(self.training.publication_contact_entity_id, self.entity.pk)
