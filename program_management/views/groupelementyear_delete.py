############################################################################
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
############################################################################
from django.http import JsonResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from base.utils.cache import ElementCache
from base.views.common import display_error_messages, display_warning_messages, display_business_messages
from program_management.business.group_element_years.detach import DetachEducationGroupYearStrategy, \
    DetachLearningUnitYearStrategy
from program_management.ddd.domain.program_tree import PATH_SEPARATOR
from program_management.ddd.service import detach_node_service
from program_management.forms.tree.detach import DetachNodeForm
from program_management.views.generic import GenericGroupElementYearMixin


# TODO :: to remove into OSIS-4645
class DetachGroupElementYearView(GenericGroupElementYearMixin, DeleteView):
    template_name = "group_element_year/confirm_detach_inner.html"

    permission_required = 'base.can_detach_node'
    form_class = DetachNodeForm

    @cached_property
    def strategy(self):
        obj = self.get_object()
        strategy_class = DetachEducationGroupYearStrategy if obj.child_branch else DetachLearningUnitYearStrategy
        return strategy_class(obj)

    # TODO :: [MOVED OK]
    def get_context_data(self, **kwargs):
        context = super(DetachGroupElementYearView, self).get_context_data(**kwargs)
        message_list = detach_node_service.detach_node(self.path_to_node_to_detach, commit=False)
        display_warning_messages(self.request, message_list.warnings)
        display_error_messages(self.request, message_list.errors)
        if not message_list.contains_errors():
            context['confirmation_message'] = self.confirmation_message
        return context

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

    @cached_property
    def path_to_node_to_detach(self) -> str:
        return self.request.GET.get('path')

    def get_initial(self):
        return {
            **super().get_initial(),
            'path': self.path_to_node_to_detach
        }

    def delete(self, request, *args, **kwargs):
        message_list = detach_node_service.detach_node(self.path_to_node_to_detach)
        display_business_messages(self.request, message_list.messages)

        if message_list.contains_errors():
            return JsonResponse({"error": True})

        self._remove_element_from_clipboard_if_stored(self.path_to_node_to_detach)

        return super().delete(request, *args, **kwargs)

    # TODO :: [MOVED OK]
    def _remove_element_from_clipboard_if_stored(self, path: str):
        element_cache = ElementCache(self.request.user)
        detached_element_id = int(path.split(PATH_SEPARATOR)[-1])
        if element_cache.equals(detached_element_id):
            element_cache.clear()

    # TODO :: [MOVED OK]
    def get_success_url(self):
        # We can just reload the page
        return
