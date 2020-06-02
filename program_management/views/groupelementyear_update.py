##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from base.models.group_element_year import GroupElementYear
from program_management.forms.tree.attach import GroupElementYearFormset
from program_management.views.generic import GenericGroupElementYearMixin


class UpdateGroupElementYearView(GenericGroupElementYearMixin, UpdateView):
    form_class = GroupElementYearFormset
    template_name = "group_element_year/group_element_year_comment_inner.html"

    def get_form_kwargs(self):
        """ For the creation, the group_element_year needs a parent and a child """
        kwargs = super().get_form_kwargs()

        # Formset don't use instance parameter
        if "instance" in kwargs:
            del kwargs["instance"]

        kwargs["queryset"] = GroupElementYear.objects.filter(id=self.kwargs["group_element_year_id"])

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = context["form"]
        if len(context["formset"]) > 0:
            context['is_education_group_year_formset'] = bool(context["formset"][0].instance.child_branch)
        return context

    # SuccessMessageMixin
    def get_success_message(self, cleaned_data):
        group_element_year = GroupElementYear.objects.get(id=self.kwargs["group_element_year_id"])
        return _("The link of %(acronym)s has been updated") % {'acronym': str(group_element_year.child)}

    def get_success_url(self):
        # We can just reload the page
        return
