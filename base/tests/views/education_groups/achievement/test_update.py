############################################################################
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
############################################################################
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class TestEducationGroupAchievementAction(TestCase):

    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()

        self.achievement_0 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_1 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_2 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        self.user.user_permissions.add(Permission.objects.get(codename="change_educationgroupachievement"))
        PersonEntityFactory(person=self.person, entity=self.education_group_year.management_entity)
        self.client.force_login(self.user)

    def test_form_valid_up(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"action": "up"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.order, 1)

    def test_form_valid_down(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_0.pk,
                ]), data={"action": "down"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_0.refresh_from_db()
        self.assertEqual(self.achievement_0.order, 1)

    def test_form_invalid(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"action": "not_an_action"}
        )

        self.assertEqual(response.status_code, 302)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], _("Invalid action"))


class TestUpdateEducationGroupAchievement(TestCase):

    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()

        self.achievement_0 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_1 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_2 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        self.user.user_permissions.add(Permission.objects.get(codename="change_educationgroupachievement"))
        PersonEntityFactory(person=self.person, entity=self.education_group_year.management_entity)
        self.client.force_login(self.user)

    def test_update(self):
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "update_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.code_name, code)

    def test_permission_denied(self):
        self.user.user_permissions.remove(Permission.objects.get(codename="change_educationgroupachievement"))
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "update_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 403)


class TestDeleteEducationGroupAchievement(TestCase):

    def setUp(self):

        self.education_group_year = EducationGroupYearFactory()

        self.achievement_0 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_1 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_2 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        self.user.user_permissions.add(Permission.objects.get(codename="delete_educationgroupachievement"))
        PersonEntityFactory(person=self.person, entity=self.education_group_year.management_entity)
        self.client.force_login(self.user)

    def test_delete(self):
        response = self.client.post(
            reverse(
                "delete_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_0.pk,
                ]), data={}
        )

        self.assertEqual(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            self.achievement_0.refresh_from_db()

    def test_permission_denied(self):
        self.user.user_permissions.remove(Permission.objects.get(codename="delete_educationgroupachievement"))
        response = self.client.post(
            reverse(
                "delete_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={}
        )

        self.assertEqual(response.status_code, 403)
