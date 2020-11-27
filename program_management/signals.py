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
from django.dispatch import receiver
from django.core.cache import cache

from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache
from education_group import publisher
from education_group.models.group_year import GroupYear
from program_management.models.element import Element
from program_management import publisher as publisher_pgrm_management


@receiver(publisher.group_created)
def create_element_of_group(sender, group_identity, **kwargs):
    Element.objects.get_or_create(
        group_year_id=GroupYear.objects.get(
            partial_acronym=group_identity.code,
            academic_year__year=group_identity.year
        ).pk
    )


@receiver(publisher.learning_unit_year_created)
def create_element_of_learning_unit_year(sender, learning_unit_identity, **kwargs):
    Element.objects.get_or_create(
        learning_unit_year_id=LearningUnitYear.objects.get(
            acronym=learning_unit_identity.code,
            academic_year__year=learning_unit_identity.year
        ).pk
    )


@receiver(publisher.learning_unit_year_deleted)
def delete_element_of_learning_unit_year(sender, learning_unit_identity, **kwargs):
    Element.objects.filter(
        learning_unit_year__acronym=learning_unit_identity.code,
        learning_unit_year__academic_year__year=learning_unit_identity.year
    ).delete()


@receiver(publisher.group_deleted)
def delete_element_of_group(sender, group_identity, **kwargs):
    Element.objects.filter(
        group_year__partial_acronym=group_identity.code,
        group_year__academic_year__year=group_identity.year
    ).delete()


@receiver(publisher_pgrm_management.element_detached)
def delete_element_in_cache_from_path_detached(sender, path_detached: str, **kwargs):
    if not hasattr(cache, 'keys'):
        # Standard Django's cache wrapper doesn't provide a keys function with wildcard operator.
        # Only django-redis allow that that's why we check if keys exists
        return
    cache_key = ElementCache.PREFIX_KEY.format(user="*")
    cached_items = cache.get_many(cache.keys(cache_key))
    [cache.delete(key) for key, cached in cached_items.items() if cached.get('path_to_detach') == path_detached]


@receiver(publisher.group_deleted)
@receiver(publisher.learning_unit_year_deleted)
def delete_element_in_cache_from_element_deleted(sender, **kwargs):
    if not hasattr(cache, 'keys'):
        # Standard Django's cache wrapper doesn't provide a keys function with wildcard operator.
        # Only django-redis allow that that's why we check if keys exists
        return
    identity = kwargs.get('learning_unit_identity') or kwargs.get('group_identity')
    cache_key = ElementCache.PREFIX_KEY.format(user="*")
    cached_items = cache.get_many(cache.keys(cache_key))
    [
        cache.delete(key) for key, cached in cached_items.items()
        if cached.get('element_code') == identity.code and cached.get('element_year') == identity.year
    ]
