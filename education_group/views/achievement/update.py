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
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from base.views.mixins import AjaxTemplateMixin
from education_group.forms.achievement import EducationGroupAchievementForm, \
    EducationGroupDetailedAchievementForm
from education_group.views.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from osis_role.contrib.views import PermissionRequiredMixin


class UpdateEducationGroupAchievement(PermissionRequiredMixin, AjaxTemplateMixin, EducationGroupAchievementMixin,
                                      UpdateView):
    template_name = "education_group_app/achievement/edit.html"
    form_class = EducationGroupAchievementForm
    permission_required = 'base.change_educationgroupachievement'
    raise_exception = True
    force_reload = True

    def get_permission_object(self):
        return self.get_object().education_group_year

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Achievement has been updated (with postpone)")
        return _("Achievement has been updated (without postpone)")


class UpdateEducationGroupDetailedAchievement(EducationGroupDetailedAchievementMixin, UpdateEducationGroupAchievement):
    form_class = EducationGroupDetailedAchievementForm

    def get_permission_object(self):
        return self.education_group_achievement.education_group_year
