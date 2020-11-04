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
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from education_group import publisher
from education_group.models.group_year import GroupYear
from osis_common.utils.models import get_object_or_none
from program_management.models.element import Element


@receiver(publisher.group_created)
def create_element_of_group(sender, group_identity, **kwargs):
    Element.objects.get_or_create(
        group_year_id=GroupYear.objects.get(
            partial_acronym=group_identity.code,
            academic_year__year=group_identity.year
        ).pk
    )


@receiver(publisher.learning_unit_year_created)
def create_element_of_learning_unit_year(sender, learning_unit_year_id, **kwargs):
    Element.objects.get_or_create(learning_unit_year_id=learning_unit_year_id)


@receiver(publisher.learning_unit_year_deleted)
def delete_element_of_learning_unit_year(sender, learning_unit_year_id, **kwargs):
    Element.objects.filter(learning_unit_year_id=learning_unit_year_id).delete()


@receiver(publisher.group_deleted)
def delete_element_of_group(sender, group_identity, **kwargs):
    Element.objects.filter(
        group_year__partial_acronym=group_identity.code,
        group_year__academic_year__year=group_identity.year
    ).delete()
