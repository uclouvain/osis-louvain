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
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.business.education_groups.achievement import postpone_achievements
from base.views.mixins import AjaxTemplateMixin
from education_group.forms.achievement import ActionForm
from education_group.views.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from osis_role.contrib.views import PermissionRequiredMixin


class EducationGroupAchievementAction(PermissionRequiredMixin, EducationGroupAchievementMixin, AjaxTemplateMixin,
                                      FormView):
    form_class = ActionForm
    permission_required = 'base.change_educationgroupachievement'
    raise_exception = True
    template_name = "education_group_app/achievement/order.html"
    force_reload = True

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data["action"] = self.request.GET.get('action')
        return initial_data

    @cached_property
    def object(self):
        return self.get_object()

    def form_valid(self, form):
        if form.is_up():
            self.get_object().up()
        elif form.is_down():
            self.get_object().down()
        if self.request.POST.get('to_postpone'):
            postpone_achievements(self.object.education_group_year)
        return super().form_valid(form)

    def get_permission_object(self):
        return self.get_object().education_group_year

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Achievement has been reordered (with postpone)")
        return _("Achievement has been reordered (without postpone)")


class EducationGroupDetailedAchievementAction(EducationGroupDetailedAchievementMixin, EducationGroupAchievementAction):
    def get_permission_object(self):
        return self.education_group_achievement.education_group_year

    def form_valid(self, form):
        if form.is_up():
            self.get_object().up()
        elif form.is_down():
            self.get_object().down()
        if self.request.POST.get('to_postpone'):
            postpone_achievements(self.object.education_group_achievement.education_group_year)
        return super(EducationGroupAchievementAction, self).form_valid(form)
