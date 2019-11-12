from django.utils.translation import gettext_lazy as _

from attribution.views.learning_unit.common import AttributionBaseViewMixin
from base.business.learning_units import perms
from base.forms.learning_unit.attribution_charge_repartition import AttributionForm, LecturingAttributionChargeForm, \
    PracticalAttributionChargeForm
from base.models.enums import learning_component_year_type
from base.models.learning_component_year import LearningComponentYear
from base.views.mixins import AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView


class UpdateAttributionView(AttributionBaseViewMixin, AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView):
    rules = [perms.is_eligible_to_manage_attributions]
    template_name = "learning_unit/attribution_inner.html"
    form_classes = {
        "attribution_form": AttributionForm,
        "lecturing_charge_form": LecturingAttributionChargeForm,
        "practical_charge_form": PracticalAttributionChargeForm
    }
    prefixes = {
        "attribution_form": "attribution_form",
        "lecturing_charge_form": "lecturing_form",
        "practical_charge_form": "practical_form"
    }

    def get_form_classes(self):
        form_classes = self.form_classes.copy()
        if LearningComponentYear.objects.filter(learning_unit_year=self.luy, type=None).exists():
            del form_classes["practical_charge_form"]
        return form_classes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attribution"] = self.attribution

        if self.luy.is_partim():
            qs_partim = self.luy.learningcomponentyear_set.all()
            context['partim_vol1'] = qs_partim.filter(type=learning_component_year_type.LECTURING).first()
            context['partim_vol2'] = qs_partim.filter(type=learning_component_year_type.PRACTICAL_EXERCISES).first()

        return context

    def get_form_kwargs(self, form_name):
        form_kwargs = super().get_form_kwargs(form_name)
        form_kwargs["instance"] = self.get_instance_form(form_name)
        return form_kwargs

    def get_instance_form(self, form_name):
        return {
            "attribution_form": self.attribution,
            "lecturing_charge_form": self.attribution.lecturing_charges[0] if self.attribution.lecturing_charges
            else None,
            "practical_charge_form": self.attribution.practical_charges[0] if self.attribution.practical_charges
            else None
        }.get(form_name)

    def get_success_message(self, forms):
        return _("Attribution modified for %(tutor)s (%(function)s)") % {"tutor": self.attribution.tutor.person,
                                                                         "function": _(self.attribution.function)}

    def attribution_form_valid(self, attribution_form):
        attribution_form.save()

    def lecturing_charge_form_valid(self, lecturing_charge_form):
        lecturing_charge_form.save(attribution=self.attribution)

    def practical_charge_form_valid(self, practical_charge_form):
        practical_charge_form.save(attribution=self.attribution)
