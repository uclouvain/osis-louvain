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
from typing import List

from django.core.exceptions import PermissionDenied

from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_year import EducationGroupYear


def can_postpone_achievements(education_group_year: 'EducationGroupYear') -> bool:
    return not education_group_year.academic_year.is_past


def postpone_achievements(education_group_year: "EducationGroupYear") -> None:
    if not can_postpone_achievements(education_group_year):
        raise PermissionDenied

    next_qs = EducationGroupYear.objects.filter(
        education_group=education_group_year.education_group,
        academic_year__year__gt=education_group_year.academic_year.year
    )

    achievements_to_postpone = EducationGroupAchievement.objects.filter(
        education_group_year=education_group_year
    ).prefetch_related(
        "educationgroupdetailedachievement_set"
    )

    for egy in next_qs:
        _purge_achievements(egy)
        _postpone_achievements(egy, achievements_to_postpone)


def _purge_achievements(education_group_year: 'EducationGroupYear'):
    qs = EducationGroupAchievement.objects.filter(
        education_group_year=education_group_year
    )
    for achievement in qs:
        achievement.delete()


def _postpone_achievements(
        education_group_year: 'EducationGroupYear',
        achievements: List["EducationGroupAchievement"]
) -> None:
    for achievment in achievements:
        achievment.pk = None
        achievment.id = None
        achievment.external_id = None
        achievment.changed = None
        achievment.education_group_year = education_group_year
        achievment.save()
        _postpone_detailed_achievemnt(achievment, achievment.educationgroupdetailedachievement_set.all())


def _postpone_detailed_achievemnt(
        achievement: 'EducationGroupAchievement',
        detailed_achievements: List['EducationGroupDetailedAchievement']
) -> None:
    for detailed_achievement in detailed_achievements:
        detailed_achievement.pk = None
        detailed_achievement.id = None
        detailed_achievement.external_id = None
        detailed_achievement.changed = None
        detailed_achievement.education_group_achievement = achievement
        detailed_achievement.save()
