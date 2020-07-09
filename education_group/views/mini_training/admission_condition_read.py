##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
import functools

from django.shortcuts import redirect
from django.urls import reverse

from education_group.views.mini_training.common_read import MiniTrainingRead, Tab
from education_group.views.serializers import admission_condition


class MiniTrainingReadAdmissionCondition(MiniTrainingRead):
    template_name = "education_group_app/mini_training/admission_condition_read.html"
    active_tab = Tab.ADMISSION_CONDITION

    def get(self, request, *args, **kwargs):
        if not self.have_admission_condition_tab():
            return redirect(reverse('mini_training_identification', kwargs=self.kwargs))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "admission_requirements_label": self.get_admission_requirements_label(),
            "can_edit_information":
                self.request.user.has_perm("base.change_admissioncondition", self.get_mini_training()),
            "mini_training": self.get_mini_training()
        }

    @functools.lru_cache()
    def get_mini_training(self):
        return self.get_education_group_version().offer

    def get_admission_requirements_label(self):
        return self.__get_admission_condition()['admission_requirements']

    @functools.lru_cache()
    def __get_admission_condition(self):
        mini_training = self.get_mini_training()
        return admission_condition.get_admission_condition(mini_training.acronym, mini_training.academic_year.year)
