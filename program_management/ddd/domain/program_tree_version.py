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

from program_management.ddd.business_types import *

STANDARD = ""


class ProgramTreeVersionBuilder:
    _tree_version = None

    def build_from(self, from_tree: 'ProgramTreeVersion', title_fr: str, title_en: str, version_name: str,
                   year: int) -> 'ProgramTreeVersion':
        assert isinstance(from_tree, ProgramTreeVersion)
        assert from_tree.is_standard, "Forbidden to copy from a non Standard version"
        if from_tree.is_transition:
            self.program_tree_version = self._build_from_transition(from_tree.tree, title_fr, title_en, version_name,
                                                                    year)
        else:
            self.program_tree_version = self._build_from_standard(from_tree.tree, title_fr, title_en, version_name,
                                                                  year)
        return self.program_tree_version

    def _build_from_transition(self, program_tree: 'ProgramTree', title_fr: str, title_en: str, version_name: str,
                               year: int) -> 'ProgramTreeVersion':
        program_tree_version = ProgramTreeVersion(tree=program_tree, title_fr=title_fr, title_en=title_en,
                                                  version_name=version_name, year=year, is_transition=True)
        return program_tree_version

    def _build_from_standard(self, program_tree: 'ProgramTree', title_fr: str, title_en: str, version_name: str,
                             year: int) -> 'ProgramTreeVersion':
        program_tree_version = ProgramTreeVersion(tree=program_tree, title_fr=title_fr, title_en=title_en,
                                                  version_name=version_name, year=year, is_transition=False)
        return program_tree_version


class ProgramTreeVersion:

    def __init__(
            self,
            tree: 'ProgramTree',
            version_name: str = STANDARD,
            is_transition: bool = False,
            offer: int = None,
            title_fr: str = None,
            title_en: str = None,
            year: int = None,
    ):
        self.tree = tree
        self.is_transition = is_transition
        self.version_name = version_name
        self.offer = offer
        self.title_fr = title_fr
        self.title_en = title_en
        self.year = year

    @property
    def is_standard(self):
        return self.version_name == STANDARD
