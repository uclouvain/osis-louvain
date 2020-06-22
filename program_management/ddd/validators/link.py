import osis_common.ddd.interface
from base.ddd.utils import business_validator
from program_management.ddd.business_types import *
from program_management.ddd.validators._infinite_recursivity import InfiniteRecursivityLinkValidator
from program_management.ddd.validators._node_duplication import NodeDuplicationValidator
from program_management.ddd.validators._parent_as_leaf import ParentIsNotLeafValidator
from program_management.ddd.validators._parent_child_academic_year import ParentChildSameAcademicYearValidator


class CreateLinkValidatorList(business_validator.BusinessListValidator):
    def __init__(self, parent_node: 'Node', node_to_add: 'Node'):
        self.validators = [
            ParentIsNotLeafValidator(parent_node, node_to_add),
            NodeDuplicationValidator(parent_node, node_to_add),
            ParentChildSameAcademicYearValidator(parent_node, node_to_add),
            InfiniteRecursivityLinkValidator(parent_node, node_to_add),
        ]
        super().__init__()

    def validate(self):
        error_messages = []
        for validator in self.validators:
            try:
                validator.validate()
            except osis_common.ddd.interface.BusinessExceptions as business_exception:
                error_messages.extend(business_exception.messages)

        if error_messages:
            raise osis_common.ddd.interface.BusinessExceptions(error_messages)
