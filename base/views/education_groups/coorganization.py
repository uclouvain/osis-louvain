##############################################################################
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
##############################################################################
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView, CreateView, DeleteView

from base.forms.education_group.coorganization import CoorganizationEditForm
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.views.education_groups import perms
from base.views.mixins import RulesRequiredMixin, AjaxTemplateMixin


class CommonEducationGroupOrganizationView(RulesRequiredMixin, AjaxTemplateMixin, SuccessMessageMixin):
    model = EducationGroupOrganization
    context_object_name = "coorganization"

    form_class = CoorganizationEditForm
    template_name = "education_group/organization_edit.html"

    # RulesRequiredMixin
    raise_exception = True
    rules = [perms.can_change_education_group]

    def _call_rule(self, rule):
        return rule(self.person.user, self.education_group_year)

    @cached_property
    def person(self):
        return self.request.user.person

    @cached_property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs['education_group_year_id'])

    def get_success_url(self):
        return reverse(
            'update_education_group', args=[self.kwargs["root_id"], self.kwargs["education_group_year_id"]]
        ).rstrip('/') + "#panel_coorganization"


class CreateEducationGroupOrganizationView(CommonEducationGroupOrganizationView, CreateView):
    def get_success_message(self, cleaned_data):
        return _("The coorganization has been created")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return {
            'education_group_year': self.education_group_year,
            **kwargs
        }


class UpdateEducationGroupOrganizationView(CommonEducationGroupOrganizationView, UpdateView):

    pk_url_kwarg = 'coorganization_id'

    def get_success_message(self, cleaned_data):
        return _("The coorganization modifications has been saved")


class CoorganizationDeleteView(CommonEducationGroupOrganizationView, DeleteView):
    pk_url_kwarg = "coorganization_id"
    template_name = "education_group/blocks/modal/modal_organization_confirm_delete_inner.html"
