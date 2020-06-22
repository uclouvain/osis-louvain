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
from threading import Thread
from typing import List

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

from base.models import learning_unit_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType, GroupType
from base.models.group_element_year import find_learning_unit_roots

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def publish_learning_unit_year(learning_unit_year_obj: learning_unit_year.LearningUnitYear) -> bool:
    if not all([settings.ESB_API_URL, settings.ESB_AUTHORIZATION, settings.ESB_REFRESH_PEDAGOGY_ENDPOINT,
                settings.ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT,
                settings.ESB_REFRESH_COMMON_ADMISSION_ENDPOINT]):
        raise ImproperlyConfigured('ESB_API_URL / ESB_AUTHORIZATION / ESB_REFRESH_PEDAGOGY_ENDPOINT / '
                                   'ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT /  '
                                   'ESB_REFRESH_COMMON_ADMISSION_ENDPOINT must be set in configuration')

    trainings = find_learning_unit_roots(
        [learning_unit_year_obj], return_result_params={'parents_as_instances': True}
    ).get(learning_unit_year_obj.pk, [])
    education_group_to_publish = next((training for training in trainings), None)
    if education_group_to_publish:
        t = Thread(target=_bulk_publish, args=([education_group_to_publish],))
        t.start()
    return True


def publish_education_group_year(education_group_year_obj: EducationGroupYear) -> bool:
    if not all([settings.ESB_API_URL, settings.ESB_AUTHORIZATION, settings.ESB_REFRESH_PEDAGOGY_ENDPOINT,
                settings.ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT,
                settings.ESB_REFRESH_COMMON_ADMISSION_ENDPOINT]):
        raise ImproperlyConfigured('ESB_API_URL / ESB_AUTHORIZATION / ESB_REFRESH_PEDAGOGY_ENDPOINT / '
                                   'ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT /  '
                                   'ESB_REFRESH_COMMON_ADMISSION_ENDPOINT must be set in configuration')

    trainings = find_learning_unit_roots(
        [education_group_year_obj],
        return_result_params={
            'parents_as_instances': True
        }
    ).get(education_group_year_obj.pk, [])

    education_groups_to_publish = [education_group_year_obj] + trainings \
        if education_group_year_obj.education_group_type.name != GroupType.COMMON_CORE.name \
        else trainings
    t = Thread(target=_bulk_publish, args=(education_groups_to_publish,))
    t.start()
    return True


def _bulk_publish(education_group_years: List[EducationGroupYear]) -> List[bool]:
    return [_publish(education_group_year) for education_group_year in education_group_years]


def _publish(education_group_year: EducationGroupYear) -> bool:
    publish_url = _get_url_to_publish(education_group_year)
    try:
        response = requests.get(
            publish_url,
            headers={"Authorization": settings.ESB_AUTHORIZATION},
            timeout=settings.REQUESTS_TIMEOUT
        )
        if response.status_code != HttpResponse.status_code:
            logger.info(
                "The program {acronym} has no page to publish on it".format(acronym=education_group_year.acronym)
            )
            return False
        return True
    except Exception:
        raise PublishException("Unable to publish sections for the program {acronym}".format(
            acronym=education_group_year.acronym)
        )


def _get_url_to_publish(education_group_year: EducationGroupYear) -> str:
    if education_group_year.is_main_common:
        endpoint = settings.ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT.format(year=education_group_year.academic_year.year)
    elif education_group_year.is_common:
        endpoint = settings.ESB_REFRESH_COMMON_ADMISSION_ENDPOINT.format(year=education_group_year.academic_year.year)
    else:
        code = _get_code_according_type(education_group_year)
        endpoint = settings.ESB_REFRESH_PEDAGOGY_ENDPOINT.format(
            year=education_group_year.academic_year.year,
            code=code
        )
    return "{esb_api}/{endpoint}".format(esb_api=settings.ESB_API_URL, endpoint=endpoint)


def _get_code_according_type(education_group_year: EducationGroupYear) -> str:
    code = education_group_year.acronym
    if education_group_year.is_minor:
        code = "min-{}".format(education_group_year.partial_acronym)
    elif education_group_year.is_deepening:
        code = "app-{}".format(education_group_year.partial_acronym)
    elif education_group_year.is_option or education_group_year.is_finality:
        parent = EducationGroupYear.hierarchy.filter(pk=education_group_year.pk).get_parents().get(
            education_group_type__name__in=[TrainingType.PGRM_MASTER_120.name, TrainingType.PGRM_MASTER_180_240.name]
        )
        code = "{}-{}".format(parent.acronym, education_group_year.partial_acronym)
    elif education_group_year.is_major:
        code = "fsa1ba-{}".format(education_group_year.partial_acronym)
    return code


class PublishException(Exception):
    """Some kind of problem with a publish to ESB. """
    pass
