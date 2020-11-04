from typing import List

from program_management.ddd.business_types import *
from base.models.enums.link_type import LinkTypes
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


# TODO : remove import of '_get_root_ids' (to avoid cyclic import) and re-implement function using domains identities
def load_tree_versions_from_children(
        child_element_ids: list,
        link_type: LinkTypes = None
) -> List['ProgramTreeVersion']:
    from program_management.ddd.repositories.load_tree import _get_root_ids

    root_ids = _get_root_ids(child_element_ids, link_type)
    return ProgramTreeVersionRepository.search(element_ids=list(root_ids))
