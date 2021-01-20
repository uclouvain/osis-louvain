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


class TestOrderAchievement(TestCase, TestAchievementMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_achievement_data()
        self.achievement_first = self.achievement
        self.achievement_second = self.other_achievement

        self.up_url = reverse(
            "training_achievement_actions",
            args=[
                self.education_group_year.academic_year.year,
                self.education_group_year.partial_acronym,
                self.achievement_second.id
            ]
        )
        self.down_url = reverse(
            "training_achievement_actions",
            args=[
                self.education_group_year.academic_year.year,
                self.education_group_year.partial_acronym,
                self.achievement_first.id
            ]
        )
        self.client.force_login(self.person.user)

    def test_should_up_achievement(self):
        self.client.post(self.up_url, data=self.generate_up_post_data())

        self.assertQuerysetEqual(
            EducationGroupAchievement.objects.filter(education_group_year=self.education_group_year),
            [self.achievement_second.id, self.achievement_first.id],
            transform=lambda obj: obj.id
        )

    def test_should_down_achievement(self):
        self.client.post(self.down_url, data=self.generate_down_post_data())

        self.assertQuerysetEqual(
            EducationGroupAchievement.objects.filter(education_group_year=self.education_group_year),
            [self.achievement_second.id, self.achievement_first.id],
            transform=lambda obj: obj.id
        )

    def test_should_postpone_when_postpone_parameter_set(self):
        self.client.post(self.up_url, data=self.generate_up_post_data(to_postpone=True))

        self.assert_achievements_equal(self.education_group_year, self.next_year_education_group_year)

    @classmethod
    def generate_up_post_data(cls, to_postpone=False):
        post_data = {"path": "", "action": "up"}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data

    @classmethod
    def generate_down_post_data(cls, to_postpone=False):
        post_data = {"path": "", "action": "down"}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data


class TestOrderDetailedAchievement(TestCase, TestAchievementMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_detailed_achievement_data()
        self.detailed_achievement_first = self.detailed_achievement
        self.detailed_achievement_second = self.other_detailed_achievement

        self.url = reverse(
            "training_detailed_achievement_actions",
            args=[
                self.education_group_year.academic_year.year,
                self.education_group_year.partial_acronym,
                self.achievement.id,
                self.detailed_achievement_second.id
            ]
        )
        self.client.force_login(self.person.user)

    def test_should_up_achievement(self):
        self.client.post(self.url, data=self.generate_up_post_data())
        self.assertQuerysetEqual(
            EducationGroupDetailedAchievement.objects.filter(education_group_achievement=self.achievement),
            [self.detailed_achievement_second.id, self.detailed_achievement_first.id],
            transform=lambda obj: obj.id
        )

    def test_should_postpone_when_postpone_parameter_set(self):
        self.client.post(self.url, data=self.generate_up_post_data(to_postpone=True))

        self.assert_achievements_equal(self.education_group_year, self.next_year_education_group_year)

    @classmethod
    def generate_up_post_data(cls, to_postpone=False):
        post_data = {"path": "", "action": "up"}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data
