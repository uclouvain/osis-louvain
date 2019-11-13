from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.views.learning_units.search.common import EXTERNAL_SEARCH, BaseLearningUnitSearch
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer


class ExternalLearningUnitSearch(BaseLearningUnitSearch):
    template_name = "learning_unit/search/external.html"
    search_type = EXTERNAL_SEARCH
    filterset_class = ExternalLearningUnitFilter
    serializer_class = LearningUnitDetailedSerializer
    permission_required = "base.can_access_externallearningunityear"
