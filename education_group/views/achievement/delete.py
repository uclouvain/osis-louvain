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
from base.business.education_groups.achievement import postpone_achievements
from base.views.common import display_success_messages
from education_group.views.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from base.views.mixins import DeleteViewWithDependencies
from osis_role.contrib.views import PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _


class DeleteEducationGroupAchievement(PermissionRequiredMixin, EducationGroupAchievementMixin,
                                      DeleteViewWithDependencies):
    template_name = "education_group_app/achievement/delete.html"
    permission_required = 'base.delete_educationgroupachievement'
    raise_exception = True
    force_reload = True

    def get_permission_object(self):
        return self.education_group_year

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.POST.get('to_postpone'):
            postpone_achievements(self.object.education_group_year)
        display_success_messages(self.request, self.get_success_message(None))
        return response

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Achievement has been deleted (with postpone)")
        return _("Achievement has been deleted (without postpone)")


class DeleteEducationGroupDetailedAchievement(PermissionRequiredMixin, EducationGroupDetailedAchievementMixin,
                                              DeleteViewWithDependencies):
    template_name = "education_group_app/achievement/delete.html"
    permission_required = 'base.delete_educationgroupachievement'
    raise_exception = True
    force_reload = True

    def get_permission_object(self):
        return self.education_group_year

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.POST.get('to_postpone'):
            postpone_achievements(self.object.education_group_achievement.education_group_year)
        display_success_messages(self.request, self.get_success_message(None))
        return response

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Achievement has been deleted (with postpone)")
        return _("Achievement has been deleted (without postpone)")
