############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.views.education_groups.group_element_year import perms
from base.views.mixins import FlagMixin, RulesRequiredMixin, AjaxTemplateMixin


@method_decorator(login_required, name='dispatch')
class GenericGroupElementYearMixin(FlagMixin, RulesRequiredMixin, SuccessMessageMixin, AjaxTemplateMixin):
    model = GroupElementYear
    context_object_name = "group_element_year"
    pk_url_kwarg = "group_element_year_id"

    # FlagMixin
    flag = "education_group_update"

    # RulesRequiredMixin
    raise_exception = True
    rules = [perms.can_create_group_element_year]

    def _call_rule(self, rule):
        """ The permission is computed from the education_group_year """
        return rule(self.request.user, self.education_group_year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['root'] = self.kwargs["root_id"]
        return context

    @property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("education_group_year_id"))

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))
