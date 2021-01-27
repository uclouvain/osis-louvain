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
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, UpdateView

from base.business.education_groups.admission_condition import postpone_admission_condition, \
    can_postpone_admission_condition
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.views.mixins import AjaxTemplateMixin
from education_group.forms.admission_condition import UpdateTextForm, UpdateLineFrenchForm, \
    UpdateLineEnglishForm
from education_group.views.admission_condition.common import AdmissionConditionMixin
from osis_role.contrib.views import PermissionRequiredMixin


class UpdateAdmissionCondition(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin, AdmissionConditionMixin,
                               FormView):
    template_name = "education_group_app/admission_condition/edit.html"
    permission_required = "base.change_admissioncondition"
    form_class = UpdateTextForm
    raise_exception = True
    force_reload = True

    def get_permission_object(self):
        return self.object.education_group_year

    def get_initial(self):
        return {
            'section': self.get_section(),
            'text_fr': getattr(self.object, self.get_form_text_fr_field_name()),
            'text_en': getattr(self.object, self.get_form_text_en_field_name()),
        }

    def form_valid(self, form):
        setattr(self.object, self.get_form_text_fr_field_name(), form.cleaned_data["text_fr"])
        setattr(self.object, self.get_form_text_en_field_name(), form.cleaned_data["text_en"])
        self.object.save()
        if self.request.POST.get("to_postpone"):
            fields = [self.get_form_text_en_field_name(), self.get_form_text_fr_field_name()]
            postpone_admission_condition(self.object.education_group_year, fields)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.request.GET["title"]
        context["can_postpone"] = can_postpone_admission_condition(
            self.object.education_group_year
        )
        return context

    def get_success_url(self):
        return ""

    def get_success_message(self, cleaned_data):
        if self.request.POST.get('to_postpone'):
            return _("%(title)s has been updated (with postpone)") % {"title": self.request.GET["title"]}
        return _("%(title)s has been updated (without postpone)") % {"title": self.request.GET["title"]}

    @cached_property
    def object(self) -> 'AdmissionCondition':
        return self.get_admission_condition_object()

    def get_section(self) -> str:
        return self.request.GET.get("section") or self.request.POST.get("section", "")

    def get_form_text_fr_field_name(self) -> str:
        return 'text_' + self.get_section()

    def get_form_text_en_field_name(self) -> str:
        return 'text_' + self.get_section() + '_en'


class UpdateAdmissionConditionLine(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin, UpdateView):
    template_name = "education_group_app/admission_condition/line_edit.html"
    permission_required = 'base.change_admissioncondition'
    raise_exception = True
    force_reload = True
    model = AdmissionConditionLine

    def get_permission_object(self):
        return self.get_object().admission_condition.education_group_year

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_postpone"] = can_postpone_admission_condition(
            self.get_object().admission_condition.education_group_year
        )
        context["section"] = self.object.get_section_display()
        return context

    def get_form_class(self):
        language = self.request.GET['language']
        if language == settings.LANGUAGE_CODE_EN:
            return UpdateLineEnglishForm
        return UpdateLineFrenchForm

    def get_object(self, queryset=None):
        return get_object_or_404(
            AdmissionConditionLine,
            pk=self.request.GET.get('id')
        )

    def get_success_url(self):
        return ""

    def get_success_message(self, cleaned_data):
        if self.request.POST.get('to_postpone'):
            return _("Condition has been updated (with postpone)")
        return _("Condition has been updated (without postpone)")
