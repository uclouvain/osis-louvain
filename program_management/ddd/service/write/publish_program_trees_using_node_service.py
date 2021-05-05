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
from threading import Thread
from typing import List

import requests
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from program_management.ddd.business_types import *
from program_management.ddd.command import PublishProgramTreesVersionUsingNodeCommand, GetProgramTreesFromNodeCommand
from program_management.ddd.domain import exception
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.domain.service.get_node_publish_url import GetNodePublishUrl
from program_management.ddd.repositories import program_tree as program_tree_repository
from program_management.ddd.service.read import search_program_trees_using_node_service


@transaction.atomic()
def publish_program_trees_using_node(cmd: PublishProgramTreesVersionUsingNodeCommand) -> List['ProgramTreeIdentity']:
    cmd = GetProgramTreesFromNodeCommand(code=cmd.code, year=cmd.year)
    program_trees = search_program_trees_using_node_service.search_program_trees_using_node(cmd)
    try:
        identity = ProgramTreeIdentity(code=cmd.code, year=cmd.year)
        program_tree = program_tree_repository.ProgramTreeRepository().get(identity)
        program_trees.append(program_tree)
    except exception.ProgramTreeNotFoundException:
        pass
    nodes_to_publish = [program_tree.root_node for program_tree in program_trees]
    t = Thread(target=_bulk_publish, args=(nodes_to_publish,))
    t.start()
    return [program_tree.entity_id for program_tree in program_trees]


def _bulk_publish(nodes: List['NodeGroupYear']) -> None:
    error_root_nodes_ids = []
    for node in nodes:
        publish_url = GetNodePublishUrl.get_url_from_node(node)
        try:
            __publish(publish_url)
        except Exception:
            error_root_nodes_ids.append(node.entity_id)

    if error_root_nodes_ids:
        raise PublishNodesException(node_ids=error_root_nodes_ids)


def __publish(publish_url: str):
    return requests.get(
        publish_url,
        headers={"Authorization": settings.ESB_AUTHORIZATION},
        timeout=settings.REQUESTS_TIMEOUT or 20
    )


class PublishNodesException(Exception):
    def __init__(self, node_ids: List['NodeIdentity'], *args, **kwargs):
        messages = []
        for node in node_ids:
            msg = _("Unable to publish sections for {code} - {year}").format(code=node.code, year=node.year)
            messages.append(msg)
        self.message = ','.join(messages)
        super().__init__(**kwargs)
