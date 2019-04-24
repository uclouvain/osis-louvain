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
    attribution_list = _group_attributions_by_global_id(attribution_list, global_ids)
    return list(attribution_list.values())


def _get_all_attributions_with_charges(global_ids):
    attributioncharge_prefetch = mdl_attribution.attribution_charge_new.search()\
        .filter(learning_component_year__learning_unit_year__learning_container_year__in_charge=True)\
        .select_related('learning_component_year__learning_unit_year__academic_year')

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


def _group_attributions_by_global_id(attribution_list, global_ids):
    computation_datetime = time.mktime(timezone.now().timetuple())
    attributions_grouped = {global_id: _get_default_attribution_dict(global_id, computation_datetime)
                            for global_id in global_ids} if global_ids is not None else {}

    for attribution in attribution_list:
        key = attribution.tutor.person.global_id
        attributions_grouped.setdefault(key, _get_default_attribution_dict(key, computation_datetime))
        attributions_grouped[key]['attributions'].extend(_split_attribution_by_learning_unit_year(attribution))
    return attributions_grouped


def _get_default_attribution_dict(global_id, computation_datetime):
    return {'global_id': global_id, 'computation_datetime': computation_datetime, 'attributions': []}


def _split_attribution_by_learning_unit_year(attribution):
    attribution_splitted = {}

    for attrib_charge in attribution.attribution_charges:
        component = attrib_charge.learning_component_year
        lunit_year = component.learning_unit_year

        allocation_charge_key = component.type if component.type else 'OTHER_CHARGE'

        attribution_splitted.setdefault(lunit_year.id, {
                'acronym': lunit_year.acronym,
                'title': lunit_year.complete_title,
                'title_next_yr': _get_title_next_luyr(component.learning_unit_year),
                'start_year': attribution.start_year,
                'end_year': attribution.end_year,
                'function': attribution.function,
                'year': lunit_year.academic_year.year,
                'weight': str(lunit_year.credits) if lunit_year.credits else '',
                'is_substitute': bool(attribution.substitute)
        }).update({
            allocation_charge_key: str(attrib_charge.allocation_charge)
        })

    return attribution_splitted.values()


def _get_title_next_luyr(learning_unit_yr):
    next_academic_year = mdl_base.academic_year.find_academic_year_by_year(
        learning_unit_yr.academic_year.year + 1)
    if next_academic_year:
        next_lunit_year = mdl_base.learning_unit_year.search(
            academic_year_id=next_academic_year.id,
            learning_unit=learning_unit_yr.learning_unit).first()
        return next_lunit_year.complete_title if next_lunit_year else None
    return None
