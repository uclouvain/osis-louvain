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
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView, CreateView, DeleteView
from osis_role.contrib.views import PermissionRequiredMixin

from base.forms.education_group.publication_contact import EducationGroupPublicationContactForm, \
    EducationGroupEntityPublicationContactForm
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear
from base.views.mixins import AjaxTemplateMixin


class CommonEducationGroupPublicationContactView(PermissionRequiredMixin, AjaxTemplateMixin, SuccessMessageMixin):
    model = EducationGroupPublicationContact
    context_object_name = "publication_contact"

    form_class = EducationGroupPublicationContactForm
    template_name = "education_group/blocks/modal/modal_publication_contact_edit_inner.html"

    @cached_property
    def person(self):
        return self.request.user.person

    @cached_property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs['education_group_year_id'])

    def get_success_url(self):
        query_dictionary = QueryDict('', mutable=True)
        query_dictionary.update(
            {
                'anchor': True
            }
        )

        return '{base_url}?{querystring}'.format(
            base_url=reverse(
                'education_group_general_informations',
                args=[
                    self.kwargs["root_id"],
                    self.kwargs["education_group_year_id"]
                ]
            ),
            querystring=query_dictionary.urlencode()
        )

    def get_permission_object(self):
        return self.education_group_year

    def get_permission_required(self):
        perm_name = 'base.change_commonpedagogyinformation' if self.education_group_year.is_common else \
            'base.change_pedagogyinformation'
        return (perm_name, )


class CreateEducationGroupPublicationContactView(CommonEducationGroupPublicationContactView, CreateView):
    def get_success_message(self, cleaned_data):
        return _("The contact has been created")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return {
            'education_group_year': self.education_group_year,
            **kwargs
        }


class UpdateEducationGroupPublicationContactView(CommonEducationGroupPublicationContactView, UpdateView):
    pk_url_kwarg = 'publication_contact_id'

    def get_success_message(self, cleaned_data):
        return _("The contacts modifications has been saved")


class EducationGroupPublicationContactDeleteView(CommonEducationGroupPublicationContactView, DeleteView):
    pk_url_kwarg = "publication_contact_id"
    template_name = "education_group/blocks/modal/modal_publication_contact_confirm_delete_inner.html"


class UpdateEducationGroupEntityPublicationContactView(CommonEducationGroupPublicationContactView, UpdateView):
    model = EducationGroupYear
    context_object_name = "education_group_year"

    form_class = EducationGroupEntityPublicationContactForm
    pk_url_kwarg = "education_group_year_id"
    template_name = "education_group/blocks/modal/modal_publication_contact_entity_edit_inner.html"
