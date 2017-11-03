##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import pika
import pika.exceptions
import time

from django.conf import settings
from django.db.models import Prefetch
from django.utils import timezone

from osis_common.queue import queue_sender

from attribution import models as mdl_attribution
from base import models as mdl_base
from base.models.enums import learning_unit_year_subtypes


logger = logging.getLogger(settings.DEFAULT_LOGGER)


def publish_to_portal(global_ids=None):
    attribution_list = _compute_list(global_ids)
    queue_name = settings.QUEUES.get('QUEUES_NAME', {}).get('ATTRIBUTION_RESPONSE')

    if queue_name:
        try:
            queue_sender.send_message(queue_name, attribution_list)
        except (RuntimeError, pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed,
                 pika.exceptions.AMQPError):
            logger.exception('Could not recompute attributions for portal...')
            return False
        return True
    else:
        logger.exception('Could not recompute attributions for portal because not queue name ATTRIBUTION_RESPONSE')
        return False


def _compute_list(global_ids=None):
    attribution_list = _get_all_attributions_with_charges(global_ids)
    attribution_list = _group_attributions_by_global_id(attribution_list)
    return list(attribution_list.values())


def _get_all_attributions_with_charges(global_ids):
    attributioncharge_prefetch = mdl_attribution.attribution_charge_new.search()\
        .prefetch_related(
            Prefetch('learning_component_year__learningunitcomponent_set',
                     queryset=mdl_base.learning_unit_component.search()
                        .filter(learning_unit_year__learning_container_year__in_charge=True)
                        .exclude(learning_unit_year__subtype=learning_unit_year_subtypes.PARTIM),
                     to_attr='learning_unit_components')
    )

    if global_ids is not None:
        qs = mdl_attribution.attribution_new.search(global_id=global_ids)
    else:
        qs = mdl_attribution.attribution_new.search()

    return qs.exclude(tutor__person__global_id__isnull=True)\
             .exclude(tutor__person__global_id="")\
             .prefetch_related(
                    Prefetch('attributionchargenew_set',
                             queryset=attributioncharge_prefetch,
                             to_attr='attribution_charges')
            )


def _group_attributions_by_global_id(attribution_list):
    attributions_grouped = {}
    computation_datetime = time.mktime(timezone.now().timetuple())
    for attribution in attribution_list:
        key = attribution.tutor.person.global_id
        attributions_grouped.setdefault(key, {'global_id': key,
                                              'computation_datetime': computation_datetime,
                                              'attributions': []})
        attributions_grouped[key]['attributions'].extend(_split_attribution_by_learning_unit_year(attribution))
    return attributions_grouped


def _split_attribution_by_learning_unit_year(attribution):
    attribution_splitted = {}

    for attrib_charge in attribution.attribution_charges:
        for learning_component in attrib_charge.learning_component_year.learning_unit_components:
            lunit_year = learning_component.learning_unit_year

            allocation_charge_key = attrib_charge.learning_component_year.type if attrib_charge.learning_component_year.type\
                                    else 'OTHER_CHARGE'

            attribution_splitted.setdefault(lunit_year.id, {
                    'acronym': lunit_year.acronym,
                    'title': lunit_year.title,
                    'start_year': attribution.start_year,
                    'function': attribution.function,
                    'year': lunit_year.academic_year.year,
                    'weight': str(lunit_year.credits)
            }).update({
                allocation_charge_key: str(attrib_charge.allocation_charge)
            })

    return attribution_splitted.values()
