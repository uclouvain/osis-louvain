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
from django.conf.urls import url, include

from base.views.education_groups.achievement.create import CreateEducationGroupAchievement, \
    CreateEducationGroupDetailedAchievement
from base.views.education_groups.achievement.delete import DeleteEducationGroupAchievement, \
    DeleteEducationGroupDetailedAchievement
from base.views.education_groups.achievement.detail import EducationGroupSkillsAchievements
from base.views.education_groups.achievement.update import EducationGroupAchievementAction, \
    EducationGroupDetailedAchievementAction, UpdateEducationGroupAchievement, UpdateEducationGroupDetailedAchievement, \
    EducationGroupAchievementProgramAim, EducationGroupAchievementAdditionalInformation

urlpatterns = [
    url(r'^$',
        EducationGroupSkillsAchievements.as_view(),
        name='education_group_skills_achievements'),

    url(r'^create',
        CreateEducationGroupAchievement.as_view(),
        name='create_education_group_achievement'),

    url(
        r'^program_aim',
        EducationGroupAchievementProgramAim.as_view(),
        name='education_group_achievement_program_aim',
    ),

    url(
        r'^additional_information',
        EducationGroupAchievementAdditionalInformation.as_view(),
        name='education_group_achievement_additional_information',
    ),

    url(r'^(?P<education_group_achievement_pk>[0-9]+)/', include([
        url(r'^actions$',
            EducationGroupAchievementAction.as_view(),
            name='education_group_achievements_actions'),

        url(r'^update$',
            UpdateEducationGroupAchievement.as_view(),
            name='update_education_group_achievement'),

        url(r'^delete$',
            DeleteEducationGroupAchievement.as_view(),
            name='delete_education_group_achievement'),

        url(r'^create',
            CreateEducationGroupDetailedAchievement.as_view(),
            name='create_education_group_detailed_achievement'),

        url(r'(?P<education_group_detail_achievement_pk>[0-9]+)/', include([
            url(r'^actions$',
                EducationGroupDetailedAchievementAction.as_view(),
                name='education_group_detailed_achievements_actions'),

            url(r'^update$',
                UpdateEducationGroupDetailedAchievement.as_view(),
                name='update_education_group_detailed_achievement'),

            url(r'^delete$',
                DeleteEducationGroupDetailedAchievement.as_view(),
                name='delete_education_group_detailed_achievement'),

        ]))
    ])),
]
