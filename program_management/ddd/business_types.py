from typing import TYPE_CHECKING

# FIXME :: Temporary solution ; waiting for update python to 3.8 for data structure
if TYPE_CHECKING:
    from program_management.ddd.domain.node import Node, NodeEducationGroupYear, NodeLearningUnitYear, NodeGroupYear
    from program_management.ddd.domain.program_tree import ProgramTree
    from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
    from program_management.ddd.domain.program_tree import Path
    from program_management.ddd.domain.link import Link
    from base.ddd.utils.validation_message import BusinessValidationMessage
