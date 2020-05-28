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
from typing import List
from django.db.models import Q

from base.models.group_element_year import GroupElementYear
from education_group.models.group_year import GroupYear
from program_management.ddd.command import DeleteProgramTreeVersionCommand
from program_management.ddd.repositories.load_tree import load_version
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element


def delete_program_tree_version(command: DeleteProgramTreeVersionCommand) -> None:
    education_group_versions = EducationGroupVersion.objects \
        .select_related('root_group__element').filter(offer__acronym=command.offer_acronym,
                                                      offer__academic_year__year__gte=command.year,
                                                      version_name=command.version_name,
                                                      is_transition=command.is_transition)
    # TODO : la validation ne doit pas être ici???
    # if DeleteVersionValidator(education_group_versions=education_group_versions).validate():
    _delete_version_trees(education_group_versions)


def _delete_version_trees(education_group_versions: List[EducationGroupVersion]) -> None:
    for education_group_version in education_group_versions:
        tree = load_version(education_group_version.offer.acronym,
                            education_group_version.offer.academic_year.year,
                            education_group_version.version_name,
                            education_group_version.is_transition)

        _delete_version_tree_content(tree.get_tree())

    for education_group_version in education_group_versions:
        _delete_version_root_group(education_group_version)


def _delete_version_root_group(education_group_version: EducationGroupVersion) -> None:
    group_year_to_delete = education_group_version.root_group
    education_group_version.delete()
    if not Element.objects.filter(group_year=group_year_to_delete).exists():
        group_year_to_delete.delete()


def _delete_version_tree_content(tree: 'ProgramTree') -> None:
    """
    This function will delete group year and the default structure
    """
    group_year_ids = []
    for node in tree.get_all_nodes():
        #TODO léger doute ici...
        child_links_to_delete = GroupElementYear.objects.filter(Q(parent_element__pk=node.pk) | Q(child_element__pk=node.pk))

        elt_to_delete = Element.objects.filter(pk=node.pk).first()
        if elt_to_delete:
            group_year_ids.append(elt_to_delete.group_year.id)

        for group_element_yr_to_delete in child_links_to_delete:
            group_element_yr_to_delete.delete()
        if elt_to_delete:
            elt_to_delete.delete()

    _delete_unused_group_year(group_year_ids)


def _delete_unused_group_year(group_year_ids: List[int]) -> None:
    for group_yr_id in group_year_ids:
        if not GroupElementYear.objects.filter(child_element__group_year__pk=group_yr_id).exists() and \
                not GroupElementYear.objects.filter(parent_element__group_year__pk=group_yr_id).exists() and \
                not EducationGroupVersion.objects.filter(root_group__pk=group_yr_id).exists() and \
                not Element.objects.filter(group_year__pk=group_yr_id).exists():
            # No reuse
            group_yr = GroupYear.objects.filter(pk=group_yr_id).first()
            if group_yr:
                group_yr.delete()
