##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import logging
import traceback

import requests
from django.conf import settings
from django.db.models import F, Case, When, Q, Value, CharField
from django.db.models.functions import Concat, Replace
from django.utils.functional import cached_property
from rest_framework import generics
from rest_framework.response import Response

from attribution.api.serializers.attribution import AttributionSerializer
from attribution.calendar.access_schedule_calendar import AccessScheduleCalendar
from attribution.models.attribution_charge_new import AttributionChargeNew
from base.models.person import Person

logger = logging.getLogger(settings.DEFAULT_LOGGER)


class AttributionListView(generics.ListAPIView):
    """
       Return all attributions of a specific user in a specific year
    """
    name = 'attributions'

    def list(self, request, *args, **kwargs):
        qs = AttributionChargeNew.objects.select_related(
            'attribution',
            'learning_component_year__learning_unit_year__academic_year'
        ).distinct(
            'attribution_id'
        ).filter(
            learning_component_year__learning_unit_year__academic_year__year=self.kwargs['year'],
            attribution__tutor__person=self.person,
            attribution__decision_making=''
        ).annotate(
            # Technical ID for making a match with data in EPC. Remove after refactoring...
            allocation_id=Replace('attribution__external_id', Value('osis.attribution_'), Value('')),

            code=F('learning_component_year__learning_unit_year__acronym'),
            type=F('learning_component_year__learning_unit_year__learning_container_year__container_type'),
            title_fr=Case(
                When(
                    Q(learning_component_year__learning_unit_year__learning_container_year__common_title__isnull=True) |
                    Q(learning_component_year__learning_unit_year__learning_container_year__common_title__exact=''),
                    then='learning_component_year__learning_unit_year__specific_title'
                ),
                When(
                    Q(learning_component_year__learning_unit_year__specific_title__isnull=True) |
                    Q(learning_component_year__learning_unit_year__specific_title__exact=''),
                    then='learning_component_year__learning_unit_year__learning_container_year__common_title'
                ),
                default=Concat(
                    'learning_component_year__learning_unit_year__learning_container_year__common_title',
                    Value(' - '),
                    'learning_component_year__learning_unit_year__specific_title'
                ),
                output_field=CharField(),
            ),
            title_en=Case(
                When(
                    Q(learning_component_year__learning_unit_year__learning_container_year__common_title_english__isnull=True) |  # noqa
                    Q(learning_component_year__learning_unit_year__learning_container_year__common_title_english__exact=''),  # noqa
                    then='learning_component_year__learning_unit_year__specific_title_english'
                ),
                When(
                    Q(learning_component_year__learning_unit_year__specific_title_english__isnull=True) |
                    Q(learning_component_year__learning_unit_year__specific_title_english__exact=''),
                    then='learning_component_year__learning_unit_year__learning_container_year__common_title_english'
                ),
                default=Concat(
                    'learning_component_year__learning_unit_year__learning_container_year__common_title_english',
                    Value(' - '),
                    'learning_component_year__learning_unit_year__specific_title_english'
                ),
                output_field=CharField(),
            ),
            year=F('learning_component_year__learning_unit_year__academic_year__year'),
            credits=F('learning_component_year__learning_unit_year__credits'),
            start_year=F('attribution__start_year'),
            function=F('attribution__function')
        )
        serializer = AttributionSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @cached_property
    def person(self) -> Person:
        return Person.objects.get(global_id=self.kwargs['global_id'])

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'access_schedule_calendar': AccessScheduleCalendar(),
            'attribution_charges': self.get_attribution_charges()
        }

    # TODO: Remove after find synchronization solution because make a remote call to EPC to get right value
    def get_attribution_charges(self):
        attribution_charges = []
        if not all([
            settings.EPC_API_URL, settings.EPC_API_USER, settings.EPC_API_PASSWORD,
            settings.EPC_ATTRIBUTIONS_TUTOR_ENDPOINT
        ]):
            logger.error("[Attribution API] Missing at least one env. settings (EPC_API_URL, EPC_API_USER, "
                         "EPC_API_PASSWORD, EPC_ATTRIBUTIONS_TUTOR_ENDPOINT)  ) ")
            return attribution_charges

        try:
            url = "{base_url}{endpoint}".format(
                base_url=settings.EPC_API_URL,
                endpoint=settings.EPC_ATTRIBUTIONS_TUTOR_ENDPOINT.format(
                    global_id=self.person.global_id,
                    year=self.kwargs['year']
                )
            )
            response = requests.get(url, auth=(settings.EPC_API_USER, settings.EPC_API_PASSWORD,), timeout=100)
            response.raise_for_status()
            response_data = response.json() or {}
            attribution_charges = response_data.get("tutorAllocations", [])
            # Fix when the webservice return a dictionnary in place of a list.
            # Occur when the tutor has a single attribution.
            if type(attribution_charges) is dict:
                attribution_charges = [attribution_charges]
            return attribution_charges
        except Exception:
            log_trace = traceback.format_exc()
            logger.warning('Error when returning attributions charge duration: \n {}'.format(log_trace))
        finally:
            return attribution_charges


class MyAttributionListView(AttributionListView):
    """
       Return all attributions of connected user in a specific year
    """
    name = 'my-attributions'

    @cached_property
    def person(self) -> Person:
        return self.request.user.person
