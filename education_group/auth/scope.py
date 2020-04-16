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
            Scope.IUFC.name: [
                TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                TrainingType.CERTIFICATE_OF_SUCCESS.name,
                TrainingType.CERTIFICATE_OF_HOLDING_CREDITS.name,
                TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
            ],
            Scope.DOCTORAT.name: [],
        }[scope]
