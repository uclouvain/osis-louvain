from typing import TYPE_CHECKING

# FIXME :: Temporary solution ; waiting for update python to 3.8 for data structure
if TYPE_CHECKING:
    from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear
    from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
