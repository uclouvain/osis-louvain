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
from decimal import Decimal

import pika
import pika.exceptions
from django.conf import settings

from attribution import models as mdl_attribution
from osis_common.queue import queue_sender

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def publish_to_portal(global_ids=None):
    tutor_application_list = _compute_list(global_ids)
    queue_name = settings.QUEUES.get('QUEUES_NAME', {}).get('APPLICATION_OSIS_PORTAL')
    if queue_name:
        try:
            queue_sender.send_message(queue_name, tutor_application_list)
        except (RuntimeError, pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed,
                 pika.exceptions.AMQPError):
            logger.exception('Could not recompute attributions for portal...')
            return False
        return True
    else:
        logger.exception('Could not recompute attributions for portal because not queue name ATTRIBUTION_RESPONSE')
        return False


def _compute_list(global_ids=None):
    tutor_application_list = _get_all_tutor_application(global_ids)
    tutor_application_list = _group_tutor_application_by_global_id(tutor_application_list)
    return list(tutor_application_list.values())


def _get_all_tutor_application(global_ids):
    if global_ids is not None:
        qs = mdl_attribution.tutor_application.search(global_id=global_ids)
    else:
        qs = mdl_attribution.tutor_application.search()
    return qs.exclude(tutor__person__global_id__isnull=True)\
             .exclude(tutor__person__global_id="")


def _group_tutor_application_by_global_id(tutor_application_list):
    tutor_applications_grouped = {}
    for tutor_application in tutor_application_list:
        key = tutor_application.tutor.person.global_id
        tutor_applications_grouped.setdefault(key, {'global_id': key,
                                                    'tutor_applications': []})
        tutor_applications_grouped[key]['tutor_applications'].append({'last_changed': str(tutor_application.last_changed),
                                                                      'year': tutor_application.learning_container_year.academic_year.year,
                                                                      'acronym': tutor_application.learning_container_year.acronym,
                                                                      'remark': tutor_application.remark,
                                                                      'course_summary': tutor_application.course_summary,
                                                                      'charge_lecturing_asked': str(tutor_application.volume_lecturing or Decimal('0.0')),
                                                                      'charge_practical_asked': str(tutor_application.volume_pratical_exercice or Decimal('0.0'))})
    return tutor_applications_grouped
