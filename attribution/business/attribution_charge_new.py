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

from attribution.models import attribution_charge_new
from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.attribution_new import AttributionNew
from base.models.enums import learning_component_year_type


def find_attribution_charge_new(learning_unit_year):
    return attribution_charge_new.AttributionChargeNew.objects \
        .filter(learning_component_year__learning_unit_year=learning_unit_year) \
        .select_related('learning_component_year', 'attribution__tutor__person')


def find_attribution_charge_new_by_learning_unit_year_as_dict(learning_unit_year):
    attribution_charges = find_attribution_charge_new(learning_unit_year)
    return create_attributions_dictionary(attribution_charges)


def create_attributions_dictionary(attribution_charges):
    attributions = {}
    for attribution_charge in attribution_charges:
        key = attribution_charge.attribution.id
        attribution_dict = {"person": attribution_charge.attribution.tutor.person,
                            "function": attribution_charge.attribution.function,
                            "start_year": attribution_charge.attribution.start_year,
                            "duration": attribution_charge.attribution.duration,
                            "substitute": attribution_charge.attribution.substitute}
        attributions.setdefault(key, attribution_dict) \
            .update({attribution_charge.learning_component_year.type: attribution_charge.allocation_charge})
    return attributions


# FIXME Refactor code to work with base.views.learning_units.charge_repartition.SelectAttributionView#attributions
def find_attributions_with_charges(learning_unit_year_id):
    lecturing_charges = AttributionChargeNew.objects \
        .filter(Q(learning_component_year__type=learning_component_year_type.LECTURING)
                | Q(learning_component_year__type__isnull=True))
    prefetch_lecturing_charges = Prefetch("attributionchargenew_set", queryset=lecturing_charges,
                                          to_attr="lecturing_charges")

    practical_charges = AttributionChargeNew.objects \
        .filter(learning_component_year__type=learning_component_year_type.PRACTICAL_EXERCISES)
    prefetch_practical_charges = Prefetch("attributionchargenew_set", queryset=practical_charges,
                                          to_attr="practical_charges")

    attributions = AttributionNew.objects \
        .filter(attributionchargenew__learning_component_year__learning_unit_year_id=learning_unit_year_id) \
        .distinct("id") \
        .prefetch_related(prefetch_lecturing_charges) \
        .prefetch_related(prefetch_practical_charges) \
        .select_related("tutor__person")
    return attributions
