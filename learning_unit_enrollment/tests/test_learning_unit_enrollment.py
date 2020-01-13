import random
from typing import List

from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.models.enums import learning_unit_enrollment_state
from base.models.enums.education_group_categories import Categories
from base.models.enums.offer_enrollment_state import OfferEnrollmentState
from base.models.learning_unit_enrollment import LearningUnitEnrollment
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.mixin.default_api_tests_cases_mixin import APIDefaultTestsCasesHttpGetMixin, APIFilterTestCaseData
from learning_unit_enrollment.api.serializers.learning_unit_enrollment import LearningUnitEnrollmentSerializer
from learning_unit_enrollment.api.views.learning_unit_enrollment import LearningUnitEnrollmentList


class EnrollmentsListByStudentTestCase(APIDefaultTestsCasesHttpGetMixin):

    methods_not_allowed = ['post', 'delete', 'put', 'patch']

    @classmethod
    def setUpTestData(cls):
        cls.education_group_acronym = 'DROI1BA'
        cls.registration_id = '00000001'
        cls.url = reverse(
            'learning_unit_enrollment_api_v1:enrollments-list-by-student',
            kwargs={'registration_id': cls.registration_id}
        )
        cls.offer_enrollment_states = [OfferEnrollmentState.PROVISORY.name, OfferEnrollmentState.SUBSCRIBED.name]

        for year in [2018, 2019, 2020]:
            LearningUnitEnrollmentFactory(
                offer_enrollment__student__person__user=cls.user,
                offer_enrollment__student__registration_id=cls.registration_id,
                offer_enrollment__education_group_year__academic_year__year=year,
                offer_enrollment__education_group_year__acronym=cls.education_group_acronym,
                offer_enrollment__education_group_year__education_group_type__category=Categories.TRAINING.name,
                learning_unit_year__academic_year__year=year,
                offer_enrollment__enrollment_state=random.choice(cls.offer_enrollment_states),
            )

    def get_filter_test_cases(self) -> List[APIFilterTestCaseData]:
        expected_ordering = ('learning_unit_year__acronym', 'learning_unit_year__academic_year__year')
        return [

            APIFilterTestCaseData(
                filters={'year': 2018},
                expected_result=LearningUnitEnrollmentSerializer(
                    LearningUnitEnrollment.objects.filter(learning_unit_year__academic_year__year=2018),
                    context={'request': RequestFactory().get(self.url)},
                    many=True,
                ).data,
            ),

            APIFilterTestCaseData(
                filters={'education_group_acronym': self.education_group_acronym},
                expected_result=LearningUnitEnrollmentSerializer(
                    LearningUnitEnrollment.objects.filter(
                        offer_enrollment__education_group_year__acronym=self.education_group_acronym
                    ).order_by(*expected_ordering),
                    context={'request': RequestFactory().get(self.url)},
                    many=True,
                ).data,
            ),

            APIFilterTestCaseData(
                filters={'learning_unit_enrollment_state': learning_unit_enrollment_state.ENROLLED},
                expected_result=LearningUnitEnrollmentSerializer(
                    LearningUnitEnrollment.objects.filter(
                        enrollment_state=learning_unit_enrollment_state.ENROLLED
                    ).order_by(*expected_ordering),
                    context={'request': RequestFactory().get(self.url)},
                    many=True,
                ).data,
            ),
            APIFilterTestCaseData(
                filters={'offer_enrollment_state': ','.join(self.offer_enrollment_states)},
                expected_result=LearningUnitEnrollmentSerializer(
                    LearningUnitEnrollment.objects.filter(
                        offer_enrollment__enrollment_state=OfferEnrollmentState.PROVISORY.name
                    ).order_by(*expected_ordering),
                    context={'request': RequestFactory().get(self.url)},
                    many=True,
                ).data,
            ),

        ]


class LearningUnitEnrollmentSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = 2020
        cls.learning_unit_acronym = 'LDROI1001'
        cls.url = reverse(
            'learning_unit_enrollment_api_v1:enrollments-list-by-learning-unit',
            kwargs={'year': cls.year, 'acronym': cls.learning_unit_acronym}
        )
        cls.learning_unit_enrollment = LearningUnitEnrollmentFactory(
            offer_enrollment__education_group_year__academic_year__year=cls.year,
            learning_unit_year__academic_year__year=cls.year,
            learning_unit_year__acronym=cls.learning_unit_acronym,
        )
        cls.serializer = LearningUnitEnrollmentSerializer(
            cls.learning_unit_enrollment,
            context={'request': RequestFactory().get(cls.url)}
        )

    def test_contains_expected_fields(self):
        expected_fields = [
            'registration_id',
            'student_first_name',
            'student_last_name',
            'student_email',
            'learning_unit_acronym',
            'education_group_acronym',
            'academic_year',
            'education_group_url',
            'learning_unit_url',
            'learning_unit_enrollment_state',
            'offer_enrollment_state',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_academic_year_field_is_slugified(self):
        test = self.serializer.data['academic_year']
        self.assertEqual(
            test,
            self.year
        )

    def test_ensure_education_group_type_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['learning_unit_acronym'],
            self.learning_unit_acronym
        )

    def test_pagination_max_limit(self):
        error_msg = """
            Used from Osis-portal to generate Excel file of all students enrolled to a Full/partim learniing unit.
            We need to fetch all enrollments because the Excel file is generated from the content page in Osis-portal.
            This test and the pagination_class can be removed when the Excel file will be generated in Osis.
        """
        self.assertEqual(LearningUnitEnrollmentList.pagination_class.max_limit, 1000, error_msg)
