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
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from base.business.education_groups.admission_condition import postpone_admission_condition_line, \
    can_postpone_admission_condition
from base.models.admission_condition import AdmissionConditionLine
from base.views.mixins import AjaxTemplateMixin
from education_group.forms.achievement import ActionForm
from osis_role.contrib.views import PermissionRequiredMixin


class OrderAdmissionConditionLine(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin, SingleObjectMixin,
                                  FormView):
    template_name = "education_group_app/admission_condition/line_order.html"
    permission_required = 'base.change_admissioncondition'
    raise_exception = True
    force_reload = True
    model = AdmissionConditionLine
    form_class = ActionForm

    def get_permission_object(self):
        return self.get_object().admission_condition.education_group_year

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_postpone"] = can_postpone_admission_condition(
            self.get_object().admission_condition.education_group_year
        )
        context["section"] = self.object.get_section_display()
        return context

    def get_object(self, queryset=None) -> 'AdmissionConditionLine':
        return get_object_or_404(
            AdmissionConditionLine,
            pk=self.request.GET["id"]
        )

    @cached_property
    def object(self):
        return self.get_object()

    def get_initial(self):
        initial = super().get_initial()
        initial["action"] = self.request.GET["action"]
        return initial

    def form_valid(self, form):
        action = form.cleaned_data["action"]
        if action == "up":
            self.object.up()
        elif action == "down":
            self.object.down()

        if self.request.POST.get("to_postpone"):
            postpone_admission_condition_line(
                self.object.admission_condition.education_group_year,
                self.object.section
            )
        return super().form_valid(form)

    def get_success_url(self):
        return ""

    def get_success_message(self, cleaned_data):
        if self.request.POST.get('to_postpone'):
            return _("Condition has been reordered (with postpone)")
        return _("Condition has been reordered (without postpone)")
