##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext as _

from assessments.business import score_encoding_sheet
from assessments.models.enums import score_sheet_address_choices
from assessments.tests.factories.score_sheet_address import ScoreSheetAddressFactory
from attribution.tests.factories.attribution import AttributionFactory
from base.models.enums import exam_enrollment_state as enrollment_states
from base.models.exam_enrollment import ExamEnrollment
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from base.tests.factories.session_exam_deadline import SessionExamDeadlineFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.tutor import TutorFactory
from reference.tests.factories.country import CountryFactory


class ScoreSheetAddressTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.offer_year = OfferYearFactory(academic_year=cls.academic_year)
        cls.entity_address_admin = cls._create_data_for_entity_address(score_sheet_address_choices.ENTITY_ADMINISTRATION)
        cls.entity_address_manag = cls._create_data_for_entity_address(score_sheet_address_choices.ENTITY_MANAGEMENT)
        cls.address_fields = ['location', 'postal_code', 'city', 'country', 'phone', 'fax']

    @classmethod
    def _create_data_for_entity_address(cls, entity_type):
        past_date = datetime.datetime(year=2015, month=1, day=1)
        education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        country = CountryFactory()
        entity = EntityFactory(country=country)
        EntityVersionFactory(entity=entity,
                             start_date=past_date,
                             end_date=None)
        OfferYearEntityFactory(offer_year=cls.offer_year,
                               entity=entity,
                               type=entity_type,
                               education_group_year=education_group_year)
        return entity

    def test_case_address_from_entity_administration(self):
        ScoreSheetAddressFactory(offer_year=self.offer_year,
                                 entity_address_choice=score_sheet_address_choices.ENTITY_ADMINISTRATION)
        self._assert_correct_address(self.entity_address_admin)

    def test_case_address_from_entity_management(self):
        ScoreSheetAddressFactory(offer_year=self.offer_year,
                                 entity_address_choice=score_sheet_address_choices.ENTITY_MANAGEMENT)
        self._assert_correct_address(self.entity_address_manag)

    def test_case_customized_address(self):
        address = ScoreSheetAddressFactory(offer_year=self.offer_year,
                                           entity_address_choice=None)
        self._assert_correct_address(address)

    def _assert_correct_address(self, correct_address):
        dict = score_encoding_sheet.get_score_sheet_address(self.offer_year)
        address = dict['address']

        for f in self.address_fields:
            self.assertEqual(getattr(correct_address, f), address.get(f))
        keys = address.keys()
        self.assertIn('email', keys)
        self.assertIn('recipient', keys)

    def test_get_address_as_dict(self):
        address1 = ScoreSheetAddressFactory(offer_year=self.offer_year)
        self._assert_address_fields_are_in_object(address1)
        country = CountryFactory()
        address2 = EntityFactory(country=country)
        self._assert_address_fields_are_in_object(address2)

    def _assert_address_fields_are_in_object(self, address1):
        fields = score_encoding_sheet._get_address_as_dict(address1).keys()
        for f in self.address_fields:
            self.assertIn(f, fields)

    def test_get_serialized_address(self):
        score_sheet_addr = ScoreSheetAddressFactory(offer_year=self.offer_year,
                                                    entity_address_choice=None)
        address = score_encoding_sheet._get_serialized_address(self.offer_year)
        self.assertEqual(address.get('country'), score_sheet_addr.country.name)
        for f in self.address_fields:
            self.assertIn(f, address)


class ScoreSheetDataTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.academic_year, acronym="LBIR1100",
                                                          decimal_scores=False)
        # Create tutor and score responsible
        _create_attribution(self.learning_unit_year, person=PersonFactory(last_name='Alibra', first_name='Paul'))
        _create_attribution(self.learning_unit_year, person=PersonFactory(last_name='Durant', first_name='Thomas'),
                            is_score_responsible=True)
        _create_attribution(self.learning_unit_year, person=PersonFactory(last_name='Lobradi', first_name='Pierre'))

        self.session_exam = SessionExamFactory(number_session=1, learning_unit_year=self.learning_unit_year)

        # Create three students and enrol them to learning unit year
        self.student_1 = StudentFactory(person=PersonFactory(last_name='Dupont', first_name='Jacques'))
        self.student_2 = StudentFactory(person=PersonFactory(last_name='Dupont', first_name='Axel'))
        self.student_3 = StudentFactory(person=PersonFactory(last_name='Armand', first_name='Zoe'))
        self.deadline = datetime.datetime(2017, 3, 1)
        self._build_enrollment([self.student_1, self.student_2, self.student_3], enrollment_states.ENROLLED)

        self.student_not_enrolled = StudentFactory(person=PersonFactory(last_name='Armand', first_name='Zoe'))
        self._build_enrollment([self.student_not_enrolled], enrollment_states.NOT_ENROLLED)

    def _build_enrollment(self, students, enrollment_state):
        for student in students:
            offer_enrollment = OfferEnrollmentFactory(offer_year=self.offer_year, student=student)

            SessionExamDeadlineFactory(offer_enrollment=offer_enrollment,
                                       number_session=self.session_exam.number_session,
                                       deadline=self.deadline,
                                       deadline_tutor=0)
            lu_enrollment = LearningUnitEnrollmentFactory(
                offer_enrollment=offer_enrollment,
                learning_unit_year=self.learning_unit_year
            )
            ExamEnrollmentFactory(learning_unit_enrollment=lu_enrollment,
                                  session_exam=self.session_exam,
                                  enrollment_state=enrollment_state)

    def test_scores_sheet_data_no_decimal_scores(self):
        # Get all exam enrollments
        exam_enrollments = ExamEnrollment.objects.all()
        data_computed = score_encoding_sheet.scores_sheet_data(exam_enrollments)
        # Should be a dictionary
        self.assertIsInstance(data_computed, dict)
        # Publication date should be today
        self.assertEqual(data_computed['publication_date'], timezone.now().strftime("%-d/%-m/%Y"))
        self.assertEqual(len(data_computed['learning_unit_years']), 1)
        self.assertFalse(data_computed['learning_unit_years'][0]['decimal_scores'])
        # Check the score responsible and the address
        score_responsible = data_computed['learning_unit_years'][0]['scores_responsible']
        self.assertEqual(score_responsible['first_name'], "Thomas")
        self.assertEqual(score_responsible['last_name'], "Durant")
        self.assertEqual(score_responsible['address']['city'], "Louvain-la-neuve")

    def test_scores_sheet_deadline(self):
        exam_enrollments = ExamEnrollment.objects.all()
        data_computed = score_encoding_sheet.scores_sheet_data(exam_enrollments)
        # Check the deadline for enrolled/not enrolled students
        for enrollment in data_computed['learning_unit_years'][0]['programs'][0]['enrollments']:
            if enrollment['registration_id'] in (self.student_1.registration_id, self.student_2.registration_id, self.student_3.registration_id):
                self.assertEqual(enrollment['deadline'], self.deadline.strftime(str(_('date_format'))))
            else:
                self.assertEqual(enrollment['deadline'], '')


def _create_attribution(learning_unit_year, person, is_score_responsible=False):
    PersonAddressFactory(person=person, label='PROFESSIONAL', city="Louvain-la-neuve")
    PersonAddressFactory(person=person, label='PRIVATE', city="Bruxelles")
    return AttributionFactory(
        learning_unit_year=learning_unit_year,
        tutor=TutorFactory(person=person),
        score_responsible=is_score_responsible
    )
