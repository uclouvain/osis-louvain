# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from backoffice.settings.base import LANGUAGE_CODE_EN
from program_management.ddd.business_types import *


def format_version_title(node: 'NodeGroupYear', language: str) -> str:
    if language == LANGUAGE_CODE_EN and node.version_title_en:
        return "[{}]".format(node.version_title_en)
    return "[{}]".format(node.version_title_fr) if node.version_title_fr else ''


def format_version_name(node: 'NodeGroupYear') -> str:
    return "[{}]".format(node.version_name) if node.version_name else ""


def format_version_complete_name(node: 'NodeGroupYear', language: str) -> str:
    version_name = format_version_name(node)
    if language == LANGUAGE_CODE_EN:
        return " - {} {}".format(node.version_title_en, version_name) if node.version_title_en \
            else " {}".format(version_name)
    return " - {} {}".format(node.version_title_fr, version_name) if node.version_title_fr \
        else " {}".format(version_name)
