from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from education_group.auth.scope import Scope


class TestScope(SimpleTestCase):
    def test_get_education_group_type_for_all_scope(self):
        expected_education_group_types = TrainingType.get_names() + MiniTrainingType.get_names() + GroupType.get_names()
        self.assertListEqual(
            Scope.get_education_group_types(Scope.ALL.name),
            expected_education_group_types
        )

    def test_get_education_group_type_for_iufc_scope(self):
        expected_education_group_types = [
            TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            TrainingType.CERTIFICATE_OF_SUCCESS.name,
            TrainingType.CERTIFICATE_OF_HOLDING_CREDITS.name,
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
            TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
        ]

        self.assertListEqual(
            Scope.get_education_group_types(Scope.IUFC.name),
            expected_education_group_types
        )

    def test_get_education_group_type_for_doctorat_scope(self):
        expected_education_group_types = []
        self.assertListEqual(
            Scope.get_education_group_types(Scope.DOCTORAT.name),
            expected_education_group_types
        )
