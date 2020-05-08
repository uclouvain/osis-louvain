from base.ddd.utils.business_validator import BusinessListValidator
from program_management.ddd.validators._version_name_exists import VersionNameExistsValidator


class CreateProgramTreeVersionValidatorList(BusinessListValidator):

    def __init__(self, year: int,version_name: str):
        self.validators = [
            VersionNameExistsValidator(year, version_name),
        ]
        super().__init__()
