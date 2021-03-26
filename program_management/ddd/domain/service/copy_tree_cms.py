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
from typing import Iterable

from base.business.education_groups.general_information_sections import get_general_information_labels
from base.models.education_group_year import EducationGroupYear
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from program_management.ddd.business_types import *


class CopyCms(interface.DomainService):
    def from_past_year(self, to_tree: 'ProgramTree') -> None:
        nodes_to_copy_cms = to_tree.get_mandatory_children(to_tree.root_node)
        for node in nodes_to_copy_cms:
            if node.is_group():
                _copy_group_cms_from_last_year(node.code, node.year)


def _copy_group_cms_from_last_year(code: str, year: int) -> None:
    copy_to = GroupYear.objects.get(partial_acronym=code, academic_year__year=year)
    copy_from = GroupYear.objects.get(academic_year__year=year-1, group=copy_to.group)

    cms_to_copy_from = TranslatedText.objects.filter(
        reference=copy_from.id,
        entity=entity_name.GROUP_YEAR,
        text_label__label__in=get_general_information_labels(),
    ).prefetch_related("text_label")

    _copy_cms(cms_to_copy_from, copy_to.id)


def _copy_cms(cms_to_copy_from: Iterable[TranslatedText], new_reference: int):
    for cms_to_copy in cms_to_copy_from:
        obj, created = TranslatedText.objects.update_or_create(
            reference=new_reference,
            entity=cms_to_copy.entity,
            text_label=cms_to_copy.text_label,
            language=cms_to_copy.language,
            defaults={"text": cms_to_copy.text}
        )
