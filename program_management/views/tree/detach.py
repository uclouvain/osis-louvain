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
from django.views.generic import FormView

from base.views.mixins import AjaxTemplateMixin
from program_management.ddd.repositories import load_tree
from program_management.forms.tree.detach import DetachNodeForm


class DetachNodeView(LoginRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "tree/detach_confirmation.html"
    form_class = DetachNodeForm

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'tree': load_tree.load(self.kwargs['root_id']),
        }

    def get_initial(self):
        return {
            **super().get_initial(),
            'path': self.request.GET.get('path')
        }

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return ""
