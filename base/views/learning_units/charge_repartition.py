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
from django.db.models import Prefetch
from django.db.models.functions import Concat
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.attribution_new import AttributionNew
from base.business.learning_units import perms
from base.forms.learning_unit.attribution_charge_repartition import LecturingAttributionChargeForm, \
    PracticalAttributionChargeForm
from base.models.enums import learning_component_year_type
from base.views.learning_units.attribution import AttributionBaseViewMixin, EditAttributionView


class SelectAttributionView(AttributionBaseViewMixin, TemplateView):
    template_name = "learning_unit/select_attribution.html"

    @cached_property
    def attributions(self):
        lecturing_charges = AttributionChargeNew.objects \
            .filter(learning_component_year__type=learning_component_year_type.LECTURING)
        prefetch_lecturing_charges = Prefetch("attributionchargenew_set", queryset=lecturing_charges,
                                              to_attr="lecturing_charges")

        practical_charges = AttributionChargeNew.objects \
            .filter(learning_component_year__type=learning_component_year_type.PRACTICAL_EXERCISES)
        prefetch_practical_charges = Prefetch("attributionchargenew_set", queryset=practical_charges,
                                              to_attr="practical_charges")
        attributions_to_exclude = AttributionChargeNew.objects \
            .filter(learning_component_year__learning_unit_year=self.luy) \
            .annotate(id_text=Concat("attribution__tutor__person__global_id", "attribution__function")) \
            .values_list("id_text", flat=True)

        parent_attributions = AttributionNew.objects \
            .filter(attributionchargenew__learning_component_year__learning_unit_year=self.parent_luy) \
            .distinct("id") \
            .annotate(id_text=Concat("tutor__person__global_id", "function")) \
            .exclude(id_text__in=attributions_to_exclude) \
            .prefetch_related(prefetch_lecturing_charges) \
            .prefetch_related(prefetch_practical_charges) \
            .select_related("tutor__person")
        return parent_attributions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attributions"] = self.attributions
        return context


class EditChargeRepartition(EditAttributionView):
    rules = [perms.is_eligible_to_manage_charge_repartition]
    template_name = "learning_unit/add_charge_repartition_inner.html"
    form_classes = {
        "lecturing_charge_form": LecturingAttributionChargeForm,
        "practical_charge_form": PracticalAttributionChargeForm
    }

    def get_success_message(self, forms):
        return _("Repartition modified for %(tutor)s (%(function)s)") %\
                        {"tutor": self.attribution.tutor.person,
                         "function": _(self.attribution.get_function_display())}


class AddChargeRepartition(EditAttributionView):
    rules = [perms.is_eligible_to_manage_charge_repartition]
    template_name = "learning_unit/add_charge_repartition_inner.html"
    form_classes = {
        "lecturing_charge_form": LecturingAttributionChargeForm,
        "practical_charge_form": PracticalAttributionChargeForm
    }

    @cached_property
    def get_copy_attribution(self):
        copy_attribution = self.attribution
        copy_attribution.id = None
        copy_attribution.save()
        return copy_attribution

    def lecturing_charge_form_valid(self, lecturing_charge_form):
        lecturing_charge_form.save(attribution=self.get_copy_attribution)

    def practical_charge_form_valid(self, practical_charge_form):
        practical_charge_form.save(attribution=self.get_copy_attribution)

    def get_lecturing_charge_form_initial(self):
        lecturing_allocation_charge = self.attribution.lecturing_charges[0].allocation_charge \
            if self.attribution.lecturing_charges else None
        return {"allocation_charge": lecturing_allocation_charge}

    def get_practical_charge_form_initial(self):
        practical_allocation_charge = self.attribution.practical_charges[0].allocation_charge \
            if self.attribution.practical_charges else None
        return {"allocation_charge": practical_allocation_charge}

    def get_instance_form(self, form_name):
        return None

    def get_success_message(self, forms):
        return _("Repartition added for %(tutor)s (%(function)s)") %\
                        {"tutor": self.attribution.tutor.person,
                         "function": _(self.attribution.get_function_display())}
