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
from osis_role.contrib.views import PermissionRequiredMixin

from base.views.education_groups.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from base.views.mixins import DeleteViewWithDependencies


class DeleteEducationGroupAchievement(PermissionRequiredMixin, EducationGroupAchievementMixin,
                                      DeleteViewWithDependencies):
    template_name = "education_group/delete.html"
    permission_required = 'base.delete_educationgroupachievement'
    raise_exception = True

    def get_permission_object(self):
        return self.education_group_year


class DeleteEducationGroupDetailedAchievement(PermissionRequiredMixin,
                                              EducationGroupDetailedAchievementMixin, DeleteViewWithDependencies):
    template_name = "education_group/delete.html"
    permission_required = 'base.delete_educationgroupachievement'
    raise_exception = True

    def get_permission_object(self):
        return self.education_group_year
