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
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion, ProgramTreeVersionBuilder
from program_management.ddd.repositories.persist_tree import persist_specific_version_program
from program_management.ddd.service.generate_node_code import generate_node_code
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element


def create_program_version(title_fr: str, title_en: str, version_name: str, end_year: int) -> None:
    """Devrait créer une version de programme, sur base des paramètres entrés"""
    tree_version = init_program_tree_version(title_fr, title_en, version_name, end_year)
    persist_specific_version_program(tree_version)


def init_program_tree_version(title_fr: str, title_en: str, version_name: str, end_year: int) -> ProgramTreeVersion:
    """Instancie un ProgramTreeVersion"""
    # builder = ProgramTreeVersionBuilder()
    # program_tree_version = builder.build_from(param1, param2)
    # return program_tree_version
    return ProgramTreeVersionBuilder()


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
    new_partial_acronym = generate_node_code(new_groupyear.partial_acronym, education_group_year.academic_year.year)
    new_groupyear.partial_acronym = new_partial_acronym
    new_groupyear.save()
    new_element = Element(group_year=new_groupyear)
    new_element.save()
    new_education_group_version = EducationGroupVersion(
        version_name=data["version_name"],
        title_fr=data["title_fr"],
        title_en=data["title_en"],
        offer=education_group_year,
        is_transition=False,
        root_group=new_groupyear
    )
    new_education_group_version.save()
    return new_education_group_version
