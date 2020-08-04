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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import FormView

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType
from base.views.mixins import AjaxTemplateMixin
from program_management.forms.select_type import SelectTypeForm


class SelectTypeCreateElementView(LoginRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "select_type_inner.html"
    form_class = SelectTypeForm

    def get(self, request, *args, **kwargs):
        if self.kwargs['category'] not in Categories.get_names():
            return HttpResponseBadRequest()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.kwargs['category'] not in Categories.get_names():
            return HttpResponseBadRequest()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'category': self.kwargs["category"],
            'path_to': self.request.GET.get('path_to')
        }

    def form_valid(self, form):
        self.kwargs["type"] = form.cleaned_data["name"]
        return super().form_valid(form)

    def get_success_url(self):
        url = ""
        if self.kwargs["type"] in GroupType.get_names():
            url = reverse('group_create', kwargs={'type': self.kwargs['type']})

        if self.kwargs["type"] in MiniTrainingType.get_names():
            url = reverse('mini_training_create', kwargs={'type': self.kwargs['type']})

        if self.kwargs["type"] in TrainingType.get_names():
            url = reverse('training_create', kwargs={'type': self.kwargs['type']})

        if "path_to" in self.request.GET:
            url += "?path_to={}".format(self.request.GET['path_to'])
        return url
