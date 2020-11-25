import itertools

from typing import Dict, List, Set, Callable

from program_management.ddd.business_types import *
from program_management.ddd.command import GetProgramTreesFromNodeCommand
from program_management.ddd.domain.node import NodeGroupYear, NodeIdentity
from program_management.ddd.repositories.node import NodeRepository

IndirectParentNode = NodeGroupYear


def utilizations_serializer(
        node_identity: 'NodeIdentity',
        search_program_trees_service: Callable[['GetProgramTreesFromNodeCommand'], List['ProgramTree']],
        node_repository: NodeRepository
):
    program_trees = search_program_trees_service(
        GetProgramTreesFromNodeCommand(
            code=node_identity.code,
            year=node_identity.year
        )
    )

    links_using_node = _search_links_using_node(node_repository.get(node_identity), program_trees)

    map_node_with_indirect_parents = _get_map_node_with_indirect_parents(
        direct_parents={link.parent for link in links_using_node},
        program_trees=program_trees
    )
    indirect_parents = set(itertools.chain.from_iterable(map_node_with_indirect_parents.values()))

    map_node_indirect_parents_of_indirect_parents = _get_map_node_with_indirect_parents(indirect_parents, program_trees)
    map_node_with_indirect_parents.update(map_node_indirect_parents_of_indirect_parents)

    return [
        {
            'link': link,
            'indirect_parents': [
                {
                    'node': indirect_parent,
                    'indirect_parents': [
                        {
                            'node': indirect_parent_of_indirect_parent
                        }
                        for indirect_parent_of_indirect_parent in _sort(map_node_with_indirect_parents, indirect_parent)
                    ]
                }
                for indirect_parent in _sort(map_node_with_indirect_parents, link.parent)
            ]
        }
        for link in sorted(links_using_node, key=lambda link: link.parent.code)
    ]


def _sort(map_node_with_indirect_parents: Dict['Node', Set['Node']], node: 'Node'):
    return sorted(map_node_with_indirect_parents.get(node), key=lambda n: n.title)


def _get_map_node_with_indirect_parents(
        direct_parents: Set['Node'],
        program_trees: List['ProgramTree']
) -> Dict['Node', Set['Node']]:
    return {
        direct_parent: _search_indirect_parents(direct_parent, program_trees)
        for direct_parent in direct_parents
    }


def _search_indirect_parents(direct_parent: 'Node', program_trees: List['ProgramTree']) -> List['NodeGroupYear']:
    trees_using_direct_parent = [tree for tree in program_trees if tree.contains(direct_parent)]
    indirect_parents = set()
    for tree in trees_using_direct_parent:
        indirect_parents |= set(tree.search_indirect_parents(direct_parent))
    return indirect_parents


def _search_links_using_node(node: 'Node', program_trees: List['ProgramTree']) -> Set['Link']:
    direct_parents = set()
    for tree in program_trees:
        direct_parents |= set(tree.search_links_using_node(node))
    return direct_parents
