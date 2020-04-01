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
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from base.ddd.utils.validation_message import BusinessValidationMessage
from base.models.education_group_year import EducationGroupYear
from base.utils.cache import ElementCache
from base.views.common import display_warning_messages, display_business_messages
from base.views.mixins import AjaxTemplateMixin
from program_management.business.group_element_years import management
from program_management.ddd.service import attach_node_service
from program_management.forms.tree.attach import AttachNodeForm, AttachNodeFormSet
from program_management.models.enums.node_type import NodeType


class AttachMultipleNodesView(LoginRequiredMixin, AjaxTemplateMixin, TemplateView):
    template_name = "tree/attach_inner.html"

    @cached_property
    def root_id(self):
        _root_id, *_ = self.request.GET['to_path'].split('|', 1)
        return _root_id

    @cached_property
    def elements_to_attach(self):
        return management.fetch_elements_selected(self.request.GET, self.request.user)

    def get_formset_class(self):
        return formset_factory(
            form=AttachNodeForm,
            formset=AttachNodeFormSet,
            extra=len(self.elements_to_attach)
        )

    def get_formset_kwargs(self):
        formset_kwargs = []
        for idx, element in enumerate(self.elements_to_attach):
            formset_kwargs.append({
                'node_id': element.pk,
                'node_type': NodeType.EDUCATION_GROUP.name if isinstance(element, EducationGroupYear) else
                NodeType.LEARNING_UNIT.name,
                'to_path': self.request.GET['to_path']
            })
        return formset_kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.elements_to_attach:
            context_data['formset'] = kwargs.pop('formset', None) or self.get_formset_class()(
                form_kwargs=self.get_formset_kwargs()
            )
        else:
            display_warning_messages(self.request, _("Please cut or copy an item before attach it"))
        return context_data

    def post(self, request, *args, **kwargs):
        formset = self.get_formset_class()(self.request.POST or None, form_kwargs=self.get_formset_kwargs())
        if formset.is_valid():
            return self.form_valid(formset)
        else:
            return self.form_invalid(formset)

    def form_valid(self, formset):
        messages = self.__execute_attach_node(formset)
        self.__clear_cache(messages)
        display_business_messages(self.request, messages)
        return redirect(
            reverse('education_group_read', args=[self.root_id, self.root_id])
        )

    @transaction.atomic
    def __execute_attach_node(self, formset) -> List['BusinessValidationMessage']:
        messages = []
        for form in formset:
            messages += attach_node_service.attach_node(
                self.root_id,
                form.node_id,
                form.node_type,
                form.to_path,
                **form.cleaned_data
            )
        return messages

    def __clear_cache(self, messages):
        if not BusinessValidationMessage.contains_errors(messages):
            ElementCache(self.request.user).clear()

    def form_invalid(self, formset):
        return self.render_to_response(self.get_context_data(formset=formset))
