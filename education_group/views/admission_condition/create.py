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
from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from base.business.education_groups.admission_condition import can_postpone_admission_condition
from base.models.admission_condition import AdmissionConditionLine, AdmissionCondition
from base.models.enums.admission_condition_sections import ConditionSectionsTypes
from base.views.mixins import AjaxTemplateMixin
from education_group.forms.admission_condition import CreateLineEnglishForm, \
    CreateLineFrenchForm
from education_group.views.admission_condition.common import AdmissionConditionMixin
from osis_role.contrib.views import PermissionRequiredMixin


class CreateAdmissionConditionLine(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin,
                                   AdmissionConditionMixin, CreateView):
    template_name = "education_group_app/admission_condition/line_edit.html"
    permission_required = 'base.change_admissioncondition'
    raise_exception = True
    force_reload = True
    model = AdmissionConditionLine

    def get_permission_object(self):
        return self.get_admission_condition_object().education_group_year

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_postpone"] = can_postpone_admission_condition(
            self.get_admission_condition_object().education_group_year
        )
        context["section"] = ConditionSectionsTypes.get_value(self.request.GET["section"])
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["section"] = self.request.GET["section"]
        return initial

    def form_valid(self, form):
        form.instance.admission_condition = self.get_admission_condition_object()
        return super().form_valid(form)

    def get_form_class(self):
        language = self.request.GET['language']
        if language == settings.LANGUAGE_CODE_EN:
            return CreateLineEnglishForm
        return CreateLineFrenchForm

    def get_success_url(self):
        return ""

    def get_success_message(self, cleaned_data):
        if self.request.POST.get('to_postpone'):
            return _("Condition has been created (with postpone)")
        return _("Condition has been created (without postpone)")
