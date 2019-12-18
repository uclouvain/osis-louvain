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
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from base.models import person
from program_management.business.group_element_years import perms as business_perms


def can_update_group_element_year(user, group_element_year, raise_exception=False):
    pers = get_object_or_404(person.Person, user=user)
    is_eligible = business_perms.is_eligible_to_update_group_element_year_content(
        pers, group_element_year, raise_exception=raise_exception
    )
    if not is_eligible:
        raise PermissionDenied
    return True


def can_detach_group_element_year(user, group_element_year, raise_exception=False):
    pers = get_object_or_404(person.Person, user=user)
    if not business_perms.is_eligible_to_detach_group_element_year(pers, group_element_year, raise_exception):
        raise PermissionDenied
    return True
