from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.utils.utils import ChoiceEnum


class Scope(ChoiceEnum):
    ALL = "ALL"
    IUFC = "IUFC"
    DOCTORAT = "DOCTORAT"

    @classmethod
    def get_education_group_types(cls, scope):
        return {
            Scope.ALL.name: TrainingType.get_names() + MiniTrainingType.get_names() + GroupType.get_names(),
            Scope.IUFC.name: TrainingType.continuing_education_types(),
            Scope.DOCTORAT.name: [],
        }[scope]
