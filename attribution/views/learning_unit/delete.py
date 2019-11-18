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
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from attribution.models.attribution_new import AttributionNew
from attribution.views.learning_unit.common import AttributionBaseViewMixin
from base.business.learning_units import perms
from base.views.mixins import AjaxTemplateMixin


class DeleteAttribution(AttributionBaseViewMixin, AjaxTemplateMixin, DeleteView):
    rules = [lambda luy, person: perms.is_eligible_to_manage_charge_repartition(luy, person)
             or perms.is_eligible_to_manage_attributions(luy, person)]
    model = AttributionNew
    template_name = "attribution/learning_unit/remove_charge_repartition_confirmation_inner.html"
    pk_url_kwarg = "attribution_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attribution"] = self.attribution
        return context

    def delete(self, request, *args, **kwargs):
        success_message = self.get_success_message()
        response = super().delete(request, *args, **kwargs)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self):
        return _("Attribution removed for %(tutor)s (%(function)s)") % \
               {"tutor": self.attribution.tutor.person,
                "function": _(self.attribution.get_function_display())}
