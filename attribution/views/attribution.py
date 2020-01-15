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

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from attribution.business import attribution_json, attribution_charge_new
from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.enums.function import Functions
from base.business.learning_units import perms as business_perms
from base.models.enums import learning_unit_year_subtypes
from base.models.person import Person
from base.views.common import display_warning_messages
from base.views.learning_units.common import get_common_context_learning_unit_year


class RecomputePortalSerializer(serializers.Serializer):
    global_ids = serializers.ListField(child=serializers.CharField(), required=False)


@api_view(['POST'])
def recompute_portal(request):
    serializer = RecomputePortalSerializer(data=request.data)
    if serializer.is_valid():
        global_ids = serializer.data['global_ids'] if serializer.data['global_ids'] else None
        result = attribution_json.publish_to_portal(global_ids)
        if result:
            return Response(status=status.HTTP_202_ACCEPTED)
    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    context["tab_active"] = "learning_unit_attributions"  # Corresponds to url_name
    warning_msgs = get_charge_repartition_warning_messages(context["learning_unit_year"].learning_container_year)
    display_warning_messages(request, warning_msgs)
    return render(request, "attribution/attributions.html", context)


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
