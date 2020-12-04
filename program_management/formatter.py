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
from django.http import Http404

from backoffice.settings.base import LANGUAGE_CODE_EN
from program_management.ddd.business_types import *
from program_management.ddd.domain.exception import ProgramTreeNotFoundException


def format_version_title(node: 'NodeGroupYear', language: str) -> str:
    if language == LANGUAGE_CODE_EN and node.version_title_en:
        return "[{}]".format(node.version_title_en) if node.version_title_en else ''
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


def format_program_tree_complete_title(program_tree_version: 'ProgramTreeVersion',
                                       language: str) -> str:
    try:
        node = program_tree_version.get_tree().root_node
        return "%(offer_acronym)s%(version_name)s%(title)s" % {
            'offer_acronym': node.title,
            'version_name': "[{}{}]".format(
                node.version_name,
                '-Transition' if program_tree_version.is_transition else '') if node.version_name else '',
            'title': _build_title(node, language),
            }
    except ProgramTreeNotFoundException:
        raise Http404


def _build_title(node: 'NodeGroupYear', language: str):
    if language == LANGUAGE_CODE_EN and node.offer_title_en:
        offer_title = " - {}".format(
            node.offer_title_en
        ) if node.offer_title_en else ''
    else:
        offer_title = " - {}".format(
            node.offer_title_fr
        ) if node.offer_title_fr else ''
    if language == LANGUAGE_CODE_EN and node.version_title_en:
        version_title = " [{}]".format(node.version_title_en)
    else:
        version_title = " [{}]".format(node.version_title_fr) if node.version_title_fr else ''
    return "{}{}".format(offer_title, version_title)
