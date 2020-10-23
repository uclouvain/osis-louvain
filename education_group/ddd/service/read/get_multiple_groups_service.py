from typing import List

from education_group.ddd import command
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.repository.group import GroupRepository


def get_multiple_groups(cmds: List[command.GetGroupCommand]) -> List['Group']:
    group_ids = [GroupIdentity(code=cmd.code, year=cmd.year) for cmd in cmds]
    return GroupRepository.search(entity_ids=group_ids)
