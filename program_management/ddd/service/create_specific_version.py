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


def report_specific_version_creation(data, education_group_year, end_postponement, education_group_years_list):
    next_education_group_year = education_group_year.next_year()
    if next_education_group_year:
        while next_education_group_year and next_education_group_year.academic_year.year <= end_postponement:
            education_group_years_list.append(next_education_group_year)
            create_specific_version(data, next_education_group_year)
            next_education_group_year = next_education_group_year.next_year()
    return education_group_years_list


def create_specific_version(data, education_group_year):
    version_standard = EducationGroupVersion.objects.get(
        offer=education_group_year, version_name="", is_transition=False
    )
    new_groupyear = version_standard.root_group
    new_groupyear.pk = None
    new_groupyear.save()
    new_education_group_version = EducationGroupVersion(
        version_name=data["version_name"],
        title_fr=data["title"],
        title_en=data["title_english"],
        offer=education_group_year,
        is_transition=False,
        root_group=new_groupyear
    )
    new_education_group_version.save()
    return new_education_group_version
