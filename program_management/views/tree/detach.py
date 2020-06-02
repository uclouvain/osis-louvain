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
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.utils.cache import ElementCache
from base.views.common import display_business_messages
from base.views.common import display_error_messages, display_warning_messages
from base.views.mixins import AjaxTemplateMixin
from program_management.ddd.domain.program_tree import PATH_SEPARATOR
from program_management.ddd.service import detach_node_service
from program_management.forms.tree.detach import DetachNodeForm
from program_management.views.generic import GenericGroupElementYearMixin


class DetachNodeView(GenericGroupElementYearMixin, AjaxTemplateMixin, FormView):
    template_name = "tree/detach_confirmation_inner.html"
    form_class = DetachNodeForm

    permission_required = 'base.can_detach_node'

    _object = None

    @property
    def parent_id(self):
        return self.path_to_detach.split('|')[-2]

    @property
    def child_id_to_detach(self):
        return self.path_to_detach.split('|')[-1]

    @property
    def path_to_detach(self):
        return self.request.GET.get('path')

    @property
    def root_id(self):
        return self.path_to_detach.split('|')[0]

    @property
    def confirmation_message(self):
        msg = "%(acronym)s" % {"acronym": self.object.child.acronym}
        if hasattr(self.object.child, 'partial_acronym'):
            msg = "%(partial_acronym)s - %(acronym)s" % {
                "acronym": msg,
                "partial_acronym": self.object.child.partial_acronym
            }
        return _("Are you sure you want to detach %(acronym)s ?") % {
            "acronym": msg
        }

    def get_context_data(self, **kwargs):
        context = super(DetachNodeView, self).get_context_data(**kwargs)
        message_list = detach_node_service.detach_node(self.request.GET.get('path'), commit=False)
        display_warning_messages(self.request, message_list.warnings)
        display_error_messages(self.request, message_list.errors)
        if not message_list.contains_errors():
            context['confirmation_message'] = self.confirmation_message
        return context

    def get_initial(self):
        return {
            **super().get_initial(),
            'path': self.path_to_detach
        }

    def get_object(self):
        obj = self.model.objects.filter(
            parent_id=self.parent_id
        ).filter(
            Q(child_branch_id=self.child_id_to_detach) | Q(child_leaf_id=self.child_id_to_detach)
        ).get()
        return obj

    @property
    def object(self):
        if self._object is None:
            self._object = self.get_object()
        return self._object

    def form_valid(self, form):
        message_list = form.save()
        display_business_messages(self.request, message_list.messages)
        if message_list.contains_errors():
            return self.form_invalid(form)
        self._remove_element_from_clipboard_if_stored(form.cleaned_data['path'])
        return super().form_valid(form)

    def form_invalid(self, form):
        return super(DetachNodeView, self).form_invalid(form)

    def _remove_element_from_clipboard_if_stored(self, path: str):
        element_cache = ElementCache(self.request.user)
        detached_element_id = int(path.split(PATH_SEPARATOR)[-1])
        if element_cache and element_cache.equals_element(detached_element_id):
            element_cache.clear()

    def get_success_url(self):
        # We can just reload the page
        return
