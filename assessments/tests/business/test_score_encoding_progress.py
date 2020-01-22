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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from random import randint

from django.test import TestCase

from assessments.business import score_encoding_progress
from attribution.tests.factories.attribution import AttributionFactory
from attribution.tests.models import test_attribution
from base.models.enums import number_session
from base.tests.factories.academic_calendar import AcademicCalendarExamSubmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.models import test_exam_enrollment, test_offer_enrollment, test_learning_unit_enrollment


class ScoreEncodingProgressTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.academic_calendar = AcademicCalendarExamSubmissionFactory(title="Submission of score encoding - 1",
                                                                      academic_year=cls.academic_year)
        SessionExamCalendarFactory(academic_calendar=cls.academic_calendar, number_session=number_session.ONE)

        # Offer year CHIM1BA
        cls.offer_year = OfferYearFactory(acronym="CHIM1BA", academic_year=cls.academic_year)

        cls.learning_unit_year = LearningUnitYearFactory(acronym="LBIR1210", academic_year=cls.academic_year)
        cls._create_context_exam_enrollments(cls.learning_unit_year, cls.offer_year, 10, 3)

        cls.learning_unit_year_2 = LearningUnitYearFactory(acronym="LBIR1211", academic_year=cls.academic_year)
        cls._create_context_exam_enrollments(cls.learning_unit_year_2, cls.offer_year, 5)

        # Offer year DIR2BA
        cls.offer_year_2 = OfferYearFactory(acronym="DIR2BA", academic_year=cls.academic_year)
        cls._create_context_exam_enrollments(cls.learning_unit_year, cls.offer_year_2, 8, 5)
        cls.program_manager = ProgramManagerFactory(offer_year=cls.offer_year)
        ProgramManagerFactory(offer_year=cls.offer_year_2, person=cls.program_manager.person)

        # Tutor [Tom Dupont] have an attribution to LBIR1210
        cls.tutor = TutorFactory(person=PersonFactory(last_name="Dupont", first_name="Thierry"))
        AttributionFactory(tutor=cls.tutor, learning_unit_year=cls.learning_unit_year, score_responsible=True)

    def test_get_scores_encoding_progress_program_manager(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=None,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        # Group by learning unit year
        progress_list = score_encoding_progress.group_by_learning_unit_year(progress_list)
        self.assertEqual(len(progress_list), 2)
        # Check if sort by learning unit acronym
        self.assertEqual(progress_list[0].learning_unit_year_acronym, self.learning_unit_year.acronym)
        self.assertEqual(progress_list[1].learning_unit_year_acronym, self.learning_unit_year_2.acronym)
        # Check total enrollment
        self.assertEqual(progress_list[0].total_exam_enrollments, 18)
        self.assertEqual(progress_list[1].total_exam_enrollments, 5)
        # Check progress
        self.assertEqual(progress_list[1].progress_int, 100)

    def test_get_scores_encoding_progress_program_manager_with_filter_offer_year(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=self.offer_year_2,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        self.assertEqual(len(progress_list), 1)
        self.assertEqual(progress_list[0].learning_unit_year_acronym, self.learning_unit_year.acronym)
        self.assertEqual(progress_list[0].total_exam_enrollments, 8)

    def test_get_scores_encoding_progress_with_tutors_and_score_responsible(self):
        # Create tutors
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year)
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year)

        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=self.offer_year_2,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        progress_list = score_encoding_progress.append_related_tutors_and_score_responsibles(progress_list)
        self.assertEqual(len(progress_list), 1)
        self.assertEqual(len(progress_list[0].tutors), 3)
        self.assertEqual(len(progress_list[0].score_responsibles), 1)

    def test_get_scores_encoding_progress_filter_only_incomplete(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=None,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        progress_list = score_encoding_progress.group_by_learning_unit_year(progress_list)
        self.assertEqual(len(progress_list), 2)
        progress_list = score_encoding_progress.filter_only_incomplete(progress_list)
        self.assertEqual(len(progress_list), 1)

    def test_get_scores_encoding_progress_filter_without_attribution(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=None,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        progress_list = score_encoding_progress.group_by_learning_unit_year(progress_list)
        progress_list = score_encoding_progress.append_related_tutors_and_score_responsibles(progress_list)
        self.assertEqual(len(progress_list), 2)
        progress_list = score_encoding_progress.filter_only_without_attribution(progress_list)
        self.assertEqual(len(progress_list), 1)  # LBIR1211 have no score responsible

    def test_find_related_offer_years(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.program_manager.person.user,
            offer_year_id=None,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        offer_years = list(score_encoding_progress.find_related_offer_years(progress_list))
        self.assertEqual(len(offer_years), 2)
        # Check sort by acronym
        self.assertEqual(offer_years[0].acronym, self.offer_year.acronym)
        self.assertEqual(offer_years[1].acronym, self.offer_year_2.acronym)

    def test_find_related_tutors(self):
        # Create tutors
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year)
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year)
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year_2)
        test_attribution.create_attribution(tutor=TutorFactory(), learning_unit_year=self.learning_unit_year_2)

        tutors = list(score_encoding_progress.find_related_tutors(self.program_manager.person.user, self.academic_year,
                                                                  number_session.ONE))
        self.assertEqual(len(tutors), 5)

    def test_order_find_related_tutors_somebody(self):
        # Create tutor - Dupont Tom
        tutor_five = TutorFactory(person=PersonFactory(last_name='Dupont', first_name='Tom'))
        test_attribution.create_attribution(tutor=tutor_five, learning_unit_year=self.learning_unit_year)
        # Create tutor - Dupont Albert
        tutor_third = TutorFactory(person=PersonFactory(last_name='Dupont', first_name='Albert'))
        test_attribution.create_attribution(tutor=tutor_third, learning_unit_year=self.learning_unit_year)
        # Create tutor - Armand Zoe
        tutor_second = TutorFactory(person=PersonFactory(last_name='Armand', first_name='Zoe'))
        test_attribution.create_attribution(tutor=tutor_second, learning_unit_year=self.learning_unit_year_2)
        # Create tutor - SOMEBODY_GID [Specific case: Must be at top of list - Global_id: 99999998]
        tutor_first = TutorFactory(person=PersonFactory(last_name='SOMEBODY_GID', first_name='SOMEBODY_GID',
                                                        global_id='99999998'))
        test_attribution.create_attribution(tutor=tutor_first, learning_unit_year=self.learning_unit_year_2)

        tutors = list(score_encoding_progress.find_related_tutors(self.program_manager.person.user, self.academic_year,
                                                                  number_session.ONE))
        self.assertEqual(len(tutors), 5)
        self.assertEqual(tutors[0], tutor_first)  # SOMEBODY_GID
        self.assertEqual(tutors[1], tutor_second)  # Armand Zoe
        self.assertEqual(tutors[2], tutor_third)  # Dupont Albert
        self.assertEqual(tutors[3], self.tutor)  # Dupont Thierry
        self.assertEqual(tutors[4], tutor_five)  # Dupont Tom

    def test_get_scores_encoding_progress_tutor(self):
        progress_list = score_encoding_progress.get_scores_encoding_progress(
            user=self.tutor.person.user,
            offer_year_id=None,
            number_session=number_session.ONE,
            academic_year=self.academic_year
        )
        # Group by learning unit year
        progress_list = score_encoding_progress.group_by_learning_unit_year(progress_list)
        self.assertEqual(len(progress_list), 1)
        # CHIM1BA - LBIR1210 (10) + DIR1BA - LBIR1210(8)
        self.assertEqual(progress_list[0].total_exam_enrollments, 18)

    @classmethod
    def _create_context_exam_enrollments(cls, learning_unit_year, offer_year, nb_enrollment=10, nb_filled=10):
        counter_filled = nb_filled
        session_exam = SessionExamFactory(number_session=number_session.ONE, learning_unit_year=learning_unit_year)
        OfferYearCalendarFactory(academic_calendar=cls.academic_calendar, offer_year=offer_year)

        for _ in range(0, nb_enrollment):
            offer_enrollment = test_offer_enrollment.create_offer_enrollment(StudentFactory(), offer_year)
            learning_unit_enrollment = test_learning_unit_enrollment.create_learning_unit_enrollment(
                offer_enrollment=offer_enrollment,
                learning_unit_year=learning_unit_year)
            exam_enrollment = test_exam_enrollment.create_exam_enrollment(session_exam, learning_unit_enrollment)
            if counter_filled:
                exam_enrollment.score_final = randint(0, 20)
                exam_enrollment.save()
                counter_filled -= 1
