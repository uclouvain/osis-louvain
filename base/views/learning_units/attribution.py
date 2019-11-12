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
import itertools

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, ugettext_lazy as _
from django.views.generic import DeleteView

from attribution.business import attribution_charge_new
from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.attribution_new import AttributionNew
from attribution.models.enums.function import Functions
from base.business.learning_units import perms, perms as business_perms
from base.forms.learning_unit.attribution_charge_repartition import AttributionForm, LecturingAttributionChargeForm, \
    PracticalAttributionChargeForm, AttributionCreationForm
from base.models.enums import learning_component_year_type, learning_unit_year_subtypes
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.common import display_warning_messages
from base.views.learning_units.common import get_common_context_learning_unit_year
from base.views.mixins import AjaxTemplateMixin, RulesRequiredMixin, MultiFormsView, MultiFormsSuccessMessageMixin


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_attributions(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id, request.user.person)

    context['attributions'] = attribution_charge_new.find_attributions_with_charges(learning_unit_year_id)
    context["can_manage_charge_repartition"] = business_perms.is_eligible_to_manage_charge_repartition(
        context["learning_unit_year"], request.user.person
    )
    context["can_manage_attribution"] = business_perms.is_eligible_to_manage_attributions(
        context["learning_unit_year"], request.user.person
    )
    warning_msgs = get_charge_repartition_warning_messages(context["learning_unit_year"].learning_container_year)
    display_warning_messages(request, warning_msgs)
    return render(request, "learning_unit/attributions.html", context)


class AttributionBaseViewMixin(RulesRequiredMixin):
    """ Generic Mixin for the update/create of Attribution """

    rules = [perms.is_eligible_to_manage_charge_repartition]

    def _call_rule(self, rule):
        return rule(self.luy, get_object_or_404(Person, user=self.request.user))

    @cached_property
    def luy(self):
        return get_object_or_404(LearningUnitYear, id=self.kwargs["learning_unit_year_id"])

    @cached_property
    def parent_luy(self):
        return self.luy.parent

    @cached_property
    def attribution(self):
        lecturing_charges = AttributionChargeNew.objects \
            .filter(Q(learning_component_year__type=learning_component_year_type.LECTURING)
                    | Q(learning_component_year__type__isnull=True))
        prefetch_lecturing_charges = Prefetch("attributionchargenew_set", queryset=lecturing_charges,
                                              to_attr="lecturing_charges")

        practical_charges = AttributionChargeNew.objects \
            .filter(learning_component_year__type=learning_component_year_type.PRACTICAL_EXERCISES)
        prefetch_practical_charges = Prefetch("attributionchargenew_set", queryset=practical_charges,
                                              to_attr="practical_charges")

        attribution = AttributionNew.objects \
            .prefetch_related(prefetch_lecturing_charges) \
            .prefetch_related(prefetch_practical_charges) \
            .select_related("tutor__person") \
            .get(id=self.kwargs["attribution_id"])
        return attribution

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["learning_unit_year"] = self.luy
        return context

    def get_success_url(self):
        return reverse("learning_unit_attributions", args=[self.kwargs["learning_unit_year_id"]])

    def get_form_kwargs(self, form_name):
        kwargs = super().get_form_kwargs(form_name)
        kwargs["learning_unit_year"] = self.luy
        return kwargs


class EditAttributionView(AttributionBaseViewMixin, AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView):
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


class AddAttribution(AttributionBaseViewMixin, AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView):
    rules = [perms.is_eligible_to_manage_attributions]
    template_name = "learning_unit/attribution_inner.html"
    form_classes = {
        "attribution_form": AttributionCreationForm,
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

    def forms_valid(self, forms):
        attribution_form = forms["attribution_form"]
        attribution_form.save()
        return super().forms_valid(forms)

    def get_success_message(self, forms):
        attribution = forms["attribution_form"].instance
        return _("Attribution added for %(tutor)s (%(function)s)") % {"tutor": attribution.tutor.person,
                                                                      "function": _(attribution.get_function_display())}

    def lecturing_charge_form_valid(self, lecturing_charge_form):
        attribution_form = self.instantiated_forms["attribution_form"]
        lecturing_charge_form.save(attribution=attribution_form.instance)

    def practical_charge_form_valid(self, practical_charge_form):
        attribution_form = self.instantiated_forms["attribution_form"]
        practical_charge_form.save(attribution=attribution_form.instance)


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


def get_charge_repartition_warning_messages(learning_container_year):
    total_charges_by_attribution_and_learning_subtype = AttributionChargeNew.objects \
        .filter(attribution__learning_container_year=learning_container_year) \
        .order_by("attribution__tutor", "attribution__function", "attribution__start_year") \
        .values("attribution__tutor", "attribution__tutor__person__first_name",
                "attribution__tutor__person__middle_name", "attribution__tutor__person__last_name",
                "attribution__function", "attribution__start_year",
                "learning_component_year__learning_unit_year__subtype") \
        .annotate(total_volume=Sum("allocation_charge"))

    charges_by_attribution = itertools.groupby(total_charges_by_attribution_and_learning_subtype,
                                               lambda rec: "{}_{}_{}".format(rec["attribution__tutor"],
                                                                             rec["attribution__start_year"],
                                                                             rec["attribution__function"]))
    msgs = []
    for attribution_key, charges in charges_by_attribution:
        charges = list(charges)
        subtype_key = "learning_component_year__learning_unit_year__subtype"
        full_total_charges = next(
            (charge["total_volume"] for charge in charges if charge[subtype_key] == learning_unit_year_subtypes.FULL),
            0)
        partim_total_charges = next(
            (charge["total_volume"] for charge in charges if charge[subtype_key] == learning_unit_year_subtypes.PARTIM),
            0)
        partim_total_charges = partim_total_charges or 0
        full_total_charges = full_total_charges or 0
        if partim_total_charges > full_total_charges:
            tutor_name = Person.get_str(charges[0]["attribution__tutor__person__first_name"],
                                        charges[0]["attribution__tutor__person__middle_name"],
                                        charges[0]["attribution__tutor__person__last_name"])
            tutor_name_with_function = "{} ({})".format(tutor_name,
                                                        getattr(Functions, charges[0]["attribution__function"]).value)
            msg = _("The sum of volumes for the partims for professor %(tutor)s is superior to the "
                    "volume of parent learning unit for this professor") % {"tutor": tutor_name_with_function}
            msgs.append(msg)
    return msgs
