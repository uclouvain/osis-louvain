##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from waffle.testutils import override_flag

from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory


@override_flag('education_group_update', active=True)
class TestPostpone(TestCase):

    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.next_academic_year = AcademicYearFactory(year=self.current_academic_year.year + 1)

        self.person = CentralManagerFactory()
        self.person.user.user_permissions.add(Permission.objects.get(codename="change_educationgroup"))
        self.person.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

        self.client.force_login(self.person.user)

        self.education_group = EducationGroupFactory(end_year=self.next_academic_year)
        self.education_group_year = TrainingFactory(academic_year=self.current_academic_year,
                                                    education_group=self.education_group)

        self.next_education_group_year = TrainingFactory(
            academic_year=self.next_academic_year,
            education_group=self.education_group,
            management_entity=self.education_group_year.management_entity
        )

        PersonEntityFactory(person=self.person, entity=self.education_group_year.management_entity)

        self.group_element_year = GroupElementYearFactory(
            parent=self.education_group_year,
            child_branch__academic_year=self.education_group_year.academic_year
        )
        self.url = reverse(
            "postpone_education_group",
            kwargs={
                "root_id": self.next_education_group_year.pk,
                "education_group_year_id": self.next_education_group_year.pk,
            }
        )

        self.redirect_url = reverse("education_group_read",
                                    args=[self.next_education_group_year.pk, self.next_education_group_year.pk])

    def test_postpone_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["warning_message"],
            _("Are you sure you want to postpone the content in %(root)s?") % {"root": self.next_education_group_year}
        )

    def test_post_with_error(self):
        self.group_element_year.delete()
        self.education_group_year.delete()
        response = self.client.post(self.url, follow=True)
        message = list(get_messages(response.wsgi_request))[0]
        self.assertEqual(message.tags, "error")

    def test_post_with_success(self):
        response = self.client.post(self.url, follow=True)

        message = list(get_messages(response.wsgi_request))[0]

        msg = _("%(count_elements)s OF(s) and %(count_links)s link(s) have been postponed with success.") % {
                'count_elements': 1,
                'count_links': 1
        }

        self.assertEqual(message.tags, "success")
        self.assertTrue(msg in message.message)
