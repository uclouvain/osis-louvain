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
from django.http import Http404
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _


from base.forms.education_group_admission import UpdateTextForm
from base.models.admission_condition import AdmissionCondition
from base.models.education_group_year import EducationGroupYear
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from osis_role.contrib.views import AjaxPermissionRequiredMixin


class UpdateCommonCondition(AjaxPermissionRequiredMixin, AjaxTemplateMixin, FormView):
    permission_required = 'base.change_commonadmissioncondition'
    form_class = UpdateTextForm

    def get_template_names(self):
        return ["education_group/condition_text_edit.html"]

    def get_form_kwargs(self):
        admission_condition = self.get_admission_condition()
        return {
            **super().get_form_kwargs(),
            'initial': {
                'section': self.get_section(),
                'text_fr': getattr(admission_condition, 'text_' + self.get_section()),
                'text_en': getattr(admission_condition, 'text_' + self.get_section() + '_en'),
            },
        }

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(),
            'title': self.get_title(),
        }

    def form_valid(self, form):
        admission_condition = self.get_admission_condition()
        setattr(admission_condition, 'text_' + self.get_section(), form.cleaned_data['text_fr'])
        setattr(admission_condition, 'text_' + self.get_section() + '_en', form.cleaned_data['text_en'])
        admission_condition.save()
        display_success_messages(self.request, _('Common admission conditions have been updated'))
        return super().form_valid(form)

    def get_section(self) -> str:
        if self.request.method == "POST":
            return self.request.POST['section']
        return self.request.GET['section']

    def get_title(self) -> str:
        return self.request.GET['title']

    def get_permission_object(self):
        try:
            return self.get_admission_condition().education_group_year
        except (AdmissionCondition.DoesNotExist, EducationGroupYear.DoesNotExist):
            raise Http404

    def get_admission_condition(self):
        raise NotImplementedError()
