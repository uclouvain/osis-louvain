from typing import TYPE_CHECKING

# FIXME :: Temporary solution ; waiting for update python to 3.8 for data structure

if TYPE_CHECKING:
    from program_management.ddd.domain.node import Node, NodeEducationGroupYear, NodeLearningUnitYear, NodeGroupYear, \
        NodeIdentity

    from program_management.ddd.domain.program_tree import ProgramTree, Path, ProgramTreeIdentity
    from program_management.ddd.domain.program_tree_version import ProgramTreeVersion, ProgramTreeVersionIdentity

    from program_management.ddd.domain.link import Link, LinkIdentity
    from base.ddd.utils.validation_message import BusinessValidationMessage
    from program_management.ddd.domain.prerequisite import PrerequisiteExpression

    from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
    from program_management.ddd.repositories.program_tree import ProgramTreeRepository
    from program_management.ddd.repositories.node import NodeRepository

    from program_management.ddd.repositories.load_tree import NodeKey


FieldValueRepresentation = str  # Type used to verbose a field value for its view representation
