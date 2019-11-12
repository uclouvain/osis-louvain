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
    template_name = "learning_unit/remove_charge_repartition_confirmation_inner.html"
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