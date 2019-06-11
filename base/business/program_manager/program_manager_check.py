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
from base.models.offer_enrollment import OfferEnrollment
from base.models.person import find_by_global_id
from base.models.program_manager import ProgramManager
from base.models.student import find_by_registration_id


def check_access_to_student(global_id, registration_id):
    student = find_by_registration_id(registration_id)
    offer_years_ids = list(OfferEnrollment.objects.filter(student=student).values_list('offer_year__id', flat=True))
    manager = find_by_global_id(global_id)
    return ProgramManager.objects.filter(person=manager, offer_year__id__in=offer_years_ids).exists()
