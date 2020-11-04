import osis_common.ddd.interface
from base.ddd.utils import business_validator
from base.ddd.utils.business_validator import MultipleExceptionBusinessListValidator
from program_management.ddd.business_types import *
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityLinkValidator
from program_management.ddd.validators._node_duplication import NodeDuplicationValidator
from program_management.ddd.validators._parent_as_leaf import ParentIsNotLeafValidator
from program_management.ddd.validators._parent_child_academic_year import ParentChildSameAcademicYearValidator


class CreateLinkValidatorList(MultipleExceptionBusinessListValidator):
    def __init__(self, parent_node: 'Node', node_to_add: 'Node'):
        self.validators = [
            ParentIsNotLeafValidator(parent_node),
            NodeDuplicationValidator(parent_node, node_to_add),
            ParentChildSameAcademicYearValidator(parent_node, node_to_add),
            InfiniteRecursivityLinkValidator(parent_node, node_to_add),
        ]
        super().__init__()
