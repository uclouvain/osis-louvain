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
from base.models.abstracts.abstract_education_group_achievement import AbstractEducationGroupAchievement
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_year import EducationGroupYear
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_detailed_achievement import EducationGroupDetailedAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class TestAchievementMixin:
    def generate_achievement_data(self):
        self.achievement = EducationGroupAchievementFactory(education_group_year__academic_year__current=True)
        self.other_achievement = EducationGroupAchievementFactory(
            education_group_year=self.achievement.education_group_year
        )
        self.education_group_year = self.achievement.education_group_year
        self.next_year_education_group_year = EducationGroupYearFactory.next_year_from(self.education_group_year)
        self.next_year_achievement = EducationGroupAchievementFactory(
            education_group_year=self.next_year_education_group_year
        )

    def generate_detailed_achievement_data(self):
        self.detailed_achievement = EducationGroupDetailedAchievementFactory(
            education_group_achievement__education_group_year__academic_year__current=True,
            order=None
        )
        self.other_detailed_achievement = EducationGroupDetailedAchievementFactory(
            education_group_achievement=self.detailed_achievement.education_group_achievement,
            order=None
        )
        self.achievement = self.detailed_achievement.education_group_achievement
        self.education_group_year = self.achievement.education_group_year
        self.next_year_education_group_year = EducationGroupYearFactory.next_year_from(self.education_group_year)

    def assert_achievements_equal(self, obj: 'EducationGroupYear', other_obj: 'EducationGroupYear') -> None:
        base_achievements = EducationGroupAchievement.objects.filter(
            education_group_year=obj
        ).prefetch_related(
            "educationgroupdetailedachievement_set"
        )

        to_compare_achievements = EducationGroupAchievement.objects.filter(
            education_group_year=other_obj
        ).prefetch_related(
            "educationgroupdetailedachievement_set"
        )

        for achievement, other_achievement in zip(base_achievements, to_compare_achievements):
            self._assert_achievement_equal(achievement, other_achievement)

            for detail_achievement, other_detail_achievement in zip(
                    achievement.educationgroupdetailedachievement_set.all(),
                    other_achievement.educationgroupdetailedachievement_set.all()
            ):
                self._assert_achievement_equal(detail_achievement, other_detail_achievement)

    def _assert_achievement_equal(
            self,
            obj: 'AbstractEducationGroupAchievement',
            other_obj: 'AbstractEducationGroupAchievement'
    ):
        fields_to_compare = ("english_text", "french_text", "code_name")
        for field in fields_to_compare:
            self.assertEqual(getattr(obj, field), getattr(other_obj, field))
