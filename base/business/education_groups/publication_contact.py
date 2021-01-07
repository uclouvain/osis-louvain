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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import List

from django.core.exceptions import PermissionDenied

from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear


def can_postpone_publication_contact(education_group_year: 'EducationGroupYear') -> bool:
    return not education_group_year.academic_year.is_past


def postpone_publication_contact(education_group_year_from: 'EducationGroupYear') -> None:
    if not can_postpone_publication_contact(education_group_year_from):
        raise PermissionDenied

    next_qs = EducationGroupYear.objects.filter(
        education_group=education_group_year_from.education_group,
        academic_year__year__gt=education_group_year_from.academic_year.year
    )

    publication_contact_to_postpone = list(EducationGroupPublicationContact.objects.filter(
        education_group_year=education_group_year_from
    ))

    for egy in next_qs:
        _purge_publication_contact(egy)
        _postpone_publication_contact(egy, publication_contact_to_postpone)


def _purge_publication_contact(education_group_year: 'EducationGroupYear') -> None:
    qs = EducationGroupPublicationContact.objects.filter(education_group_year=education_group_year)
    for publication_contact in qs:
        publication_contact.delete()


def _postpone_publication_contact(
        education_group_year: 'EducationGroupYear',
        publication_contacts: List['EducationGroupPublicationContact']
) -> None:
    for contact in publication_contacts:
        contact.pk = None
        contact.id = None
        contact.education_group_year = education_group_year
        contact.save()


def postpone_publication_entity(education_group_year_from: 'EducationGroupYear') -> None:
    if not can_postpone_publication_contact(education_group_year_from):
        raise PermissionDenied

    next_qs = EducationGroupYear.objects.filter(
        education_group=education_group_year_from.education_group,
        academic_year__year__gt=education_group_year_from.academic_year.year
    )

    publication_entity_to_postpone = education_group_year_from.publication_contact_entity

    for egy in next_qs:
        _postpone_publication_entity(egy, publication_entity_to_postpone)


def _postpone_publication_entity(egy: 'EducationGroupYear', publication_entity) -> None:
    egy.publication_contact_entity = publication_entity
    egy.save()
