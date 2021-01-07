#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from django.urls import reverse

from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.person import SuperUserPersonFactory
from education_group.tests.views.publication_contact.common import TestPublicationContactMixin


class TestCreatePublicationContact(TestCase, TestPublicationContactMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_publication_contact_data()

        self.url = reverse(
            "publication_contact_create",
            args=[self.education_group_year.academic_year.year, self.education_group_year.partial_acronym]
        )
        self.client.force_login(self.person.user)

    def test_success_post_should_create_publication_contact(self):
        count_before_create = EducationGroupPublicationContact.objects.filter(
            education_group_year=self.education_group_year
        ).count()
        self.client.post(self.url, data=self.get_post_data())

        self.assertEqual(
            EducationGroupPublicationContact.objects.filter(
                education_group_year=self.education_group_year
            ).count(),
            count_before_create + 1
        )

    def test_postpone_should_overwrite_next_years(self):
        self.client.post(self.url, data=self.get_post_data(to_postpone=True))

        self.assert_publication_contacts_equal(self.education_group_year, self.next_year_education_group_year)

    @classmethod
    def get_post_data(cls, to_postpone=False):
        post_data = {
            "type": PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name,
            "email": "test@osis.COM"
        }
        if to_postpone:
            post_data["to_postone"] = True
        return post_data
