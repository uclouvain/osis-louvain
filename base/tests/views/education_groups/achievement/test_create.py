############################################################################
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
############################################################################
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class TestCreateEducationGroupAchievement(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        cls.user = UserFactory()
        cls.person = PersonWithPermissionsFactory(
            'view_educationgroup',
            'add_educationgroupachievement',
            user=cls.user
        )
        PersonEntityFactory(person=cls.person, entity=cls.education_group_year.management_entity)

    def setUp(self):
        self.client.force_login(self.user)

    def test_create(self):
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "create_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(EducationGroupAchievement.objects.filter(education_group_year=self.education_group_year).count(), 1)

    def test_create_detailed_achievement(self):
        code = "The life is like a box of chocolates"
        achievement = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        response = self.client.post(
            reverse(
                "create_education_group_detailed_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    achievement.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(EducationGroupDetailedAchievement.objects.filter(education_group_achievement=achievement).count(), 1)

    def test_permission_denied(self):
        self.user.user_permissions.remove(Permission.objects.get(codename="add_educationgroupachievement"))
        code = "The life is like a box of chocolates"

        response = self.client.post(
            reverse(
                "create_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 403)
