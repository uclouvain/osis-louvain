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
from django.urls import reverse
from django.views.generic import CreateView

from base.forms.education_group.achievement import EducationGroupAchievementForm, EducationGroupDetailedAchievementForm
from base.views.education_groups.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from base.views.mixins import AjaxTemplateMixin
from education_group.views.proxy.read import Tab
from osis_role.contrib.views import PermissionRequiredMixin


class CreateEducationGroupAchievement(PermissionRequiredMixin, AjaxTemplateMixin, EducationGroupAchievementMixin,
                                      CreateView):
    template_name = "education_group/blocks/form/update_achievement.html"
    form_class = EducationGroupAchievementForm
    permission_required = 'base.add_educationgroupachievement'
    force_reload = True

    def form_valid(self, form):
        form.instance.education_group_year = self.education_group_year
        return super().form_valid(form)

    def get_permission_object(self):
        return self.education_group_year

    def get_success_url(self):
        prefix = 'training_' if self.education_group_year.is_training() else 'mini_training_'
        return reverse(
            prefix + 'skills_achievements', args=[self.kwargs['year'], self.kwargs['code']]
        ) + '?path={}&tab={}#achievement_{}'.format(
            self.request.POST['path'], Tab.SKILLS_ACHIEVEMENTS, str(self.object.pk)
        )


class CreateEducationGroupDetailedAchievement(PermissionRequiredMixin, AjaxTemplateMixin,
                                              EducationGroupDetailedAchievementMixin, CreateView):
    form_class = EducationGroupDetailedAchievementForm
    template_name = "education_group/blocks/form/update_achievement.html"
    permission_required = 'base.add_educationgroupachievement'
    force_reload = True

    def form_valid(self, form):
        form.instance.education_group_achievement = self.education_group_achievement
        return super().form_valid(form)

    def get_permission_object(self):
        return self.education_group_year

    def get_success_url(self):
        prefix = 'training_' if self.education_group_year.is_training() else 'mini_training_'
        return reverse(
            prefix + 'skills_achievements', args=[self.kwargs['year'], self.kwargs['code']]
        ) + '?path={}&tab={}#detail_achievements_{}'.format(
            self.request.POST['path'], Tab.SKILLS_ACHIEVEMENTS, self.object.pk
        )
