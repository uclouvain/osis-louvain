##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from program_management.models.education_group_version import EducationGroupVersion


def check_existing_version(version_name: str, education_group_year_id: int) -> bool:
    return EducationGroupVersion.objects.filter(version_name=version_name, offer__id=education_group_year_id).exists()


def find_last_existed_version(education_group_year, version_name):
    return EducationGroupVersion.objects.filter(
        version_name=version_name, offer__education_group=education_group_year.education_group,
        offer__academic_year__year__lt=education_group_year.academic_year.year).order_by('offer__academic_year').last()
