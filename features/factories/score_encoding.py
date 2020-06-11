import random

import factory

from base.models.academic_year import current_academic_year
from base.models.enums import learning_container_year_types
from base.models.learning_unit_year import LearningUnitYear
from base.models.program_manager import ProgramManager
from base.models.student import Student
from base.tests.factories.academic_calendar import AcademicCalendarExamSubmissionFactory
from base.tests.factories.exam_enrollment import ExamEnrollmentFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.tests.factories.session_examen import SessionExamFactory


class ScoreEncodingFactory:
    def __init__(self):
        current_acy = current_academic_year()
        self.students = list(Student.objects.all())

        self.learning_units = list(LearningUnitYear.objects.filter(
            academic_year=current_acy,
            learning_container_year__container_type=learning_container_year_types.COURSE
        )[0:20])
        self.program_managers = ProgramManager.objects.all().select_related("offer_year")
        self.offers = [manager.offer_year for manager in self.program_managers]

        academic_calendar = AcademicCalendarExamSubmissionFactory(academic_year__current=True)
        session_exam_calendar = SessionExamCalendarFactory(academic_calendar=academic_calendar)

        for offer in self.offers:
            self.enroll_students_to_offer(academic_calendar, offer, session_exam_calendar)

    def enroll_students_to_offer(self, academic_calendar, offer, session_exam_calendar):
        OfferYearCalendarFactory(academic_calendar=academic_calendar, offer_year=offer)
        students = random.sample(self.students, 20)
        offer_enrollments = OfferEnrollmentFactory.create_batch(
            len(students),
            offer_year=offer,
            education_group_year=None,
            student=factory.Iterator(students)
        )

        learning_units = random.sample(self.learning_units, 5)
        for lu in learning_units:
            self.enroll_students_to_learning_unit(lu, offer, offer_enrollments, session_exam_calendar)

    def enroll_students_to_learning_unit(self, lu, offer, offer_enrollments, session_exam_calendar):
        lu_enrollments = LearningUnitEnrollmentFactory.create_batch(
            len(offer_enrollments),
            learning_unit_year=lu,
            offer_enrollment=factory.Iterator(offer_enrollments)
        )
        session_exam = SessionExamFactory(
            learning_unit_year=lu,
            number_session=session_exam_calendar.number_session,
            offer_year=offer
        )
        ExamEnrollmentFactory.create_batch(
            len(lu_enrollments),
            learning_unit_enrollment=factory.Iterator(lu_enrollments),
            session_exam=session_exam
        )
