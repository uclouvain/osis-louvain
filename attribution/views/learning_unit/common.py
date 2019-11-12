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
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property

from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.attribution_new import AttributionNew
from base.business.learning_units import perms
from base.models.enums import learning_component_year_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.mixins import RulesRequiredMixin


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
