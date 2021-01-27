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
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from base.business.education_groups.admission_condition import postpone_admission_condition_line, \
    can_postpone_admission_condition
from base.models.admission_condition import AdmissionConditionLine
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from osis_role.contrib.views import PermissionRequiredMixin


class DeleteAdmissionConditionLine(PermissionRequiredMixin, AjaxTemplateMixin, DeleteView):
    template_name = "education_group_app/admission_condition/line_delete.html"
    permission_required = 'base.change_admissioncondition'
    raise_exception = True
    force_reload = True
    model = AdmissionConditionLine

    def get_permission_object(self):
        return self.get_object().admission_condition.education_group_year

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.POST.get("to_postpone"):
            postpone_admission_condition_line(
                self.object.admission_condition.education_group_year,
                self.object.section
            )
        display_success_messages(self.request, self.get_success_message(None))
        return response

    def get_object(self, queryset=None) -> 'AdmissionConditionLine':
        return get_object_or_404(
            AdmissionConditionLine,
            pk=self.request.GET.get('id')
        )

    def get_success_url(self):
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_postpone"] = can_postpone_admission_condition(
            self.get_object().admission_condition.education_group_year
        )
        context["section"] = self.object.get_section_display()
        return context

    def get_success_message(self, cleaned_data):
        if self.request.POST.get('to_postpone'):
            return _("Condition has been removed (with postpone)")
        return _("Condition has been removed (without postpone)")
