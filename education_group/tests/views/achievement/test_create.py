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

from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.tests.factories.person import SuperUserPersonFactory
from education_group.tests.views.achievement.common import TestAchievementMixin


class TestCreateAchievement(TestCase, TestAchievementMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_achievement_data()
        self.url = reverse(
            "training_achievement_create",
            args=[self.education_group_year.academic_year.year, self.education_group_year.partial_acronym]
        )
        self.client.force_login(self.person.user)

    def test_should_create_achievement(self):
        count_before_create = EducationGroupAchievement.objects.filter(
            education_group_year=self.education_group_year
        ).count()
        self.client.post(self.url, data=self.generate_post_data())

        self.assertEqual(
            EducationGroupAchievement.objects.filter(education_group_year=self.education_group_year).count(),
            count_before_create + 1
        )

    def test_should_postpone_creation_when_postpone_parameter_set(self):
        self.client.post(self.url, data=self.generate_post_data(to_postpone=True))

        self.assert_achievements_equal(self.education_group_year, self.next_year_education_group_year)

    @classmethod
    def generate_post_data(cls, to_postpone=False):
        post_data = {"code_name": ".", "french_text": "Texte en fr", "english_text": "Text in en", "path": ""}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data


class TestCreateDetailedAchievement(TestCase, TestAchievementMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_detailed_achievement_data()
        self.url = reverse(
            "training_detailed_achievement_create",
            args=[
                self.education_group_year.academic_year.year,
                self.education_group_year.partial_acronym,
                self.achievement.id
            ]
        )
        self.client.force_login(self.person.user)

    def test_should_create_achievement(self):
        count_before_create = EducationGroupDetailedAchievement.objects.filter(
            education_group_achievement=self.achievement
        ) .count()

        self.client.post(self.url, data=self.generate_post_data())

        self.assertEqual(
            EducationGroupDetailedAchievement.objects.filter(
                education_group_achievement=self.achievement
            ) .count(),
            count_before_create + 1
        )

    def test_should_postpone_creation_when_postpone_parameter_set(self):
        self.client.post(self.url, data=self.generate_post_data(to_postpone=True))

        self.assert_achievements_equal(self.education_group_year, self.next_year_education_group_year)

    @classmethod
    def generate_post_data(cls, to_postpone=False):
        post_data = {"code_name": ".", "french_text": "Texte en fr", "english_text": "Text in en", "path": ""}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data
