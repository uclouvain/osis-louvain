##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Person(models.Model):
    GENDER_CHOICES = (
        ('F',_('Female')),
        ('M',_('Male')),
        ('U',_('Unknown')))

    external_id = models.CharField(max_length = 40,blank = True, null = True)
    user        = models.OneToOneField(User, on_delete=models.CASCADE, null = True)
    global_id   = models.CharField(max_length = 10,blank = True, null = True)
    gender      = models.CharField(max_length = 1, blank = True, null = True, choices = GENDER_CHOICES, default = 'U')
    national_id = models.CharField(max_length = 25,blank = True, null = True)
    first_name = models.CharField(max_length = 50,blank = True, null = True)
    middle_name = models.CharField(max_length = 50,blank = True, null = True)
    last_name = models.CharField(max_length = 50,blank = True, null = True)

    def username(self):
        if self.user is None :
            return None
        return self.user.username

    def find_person(person_id):
        return Person.objects.get(id=person_id)

    def __str__(self):
        first_name = ""
        middle_name = ""
        last_name = ""
        if self.first_name is None :
            first_name = ""
        if self.middle_name is None :
            middle_name = ""
        if self.last_name is None :
            last_name = ""
        return u"%s %s, %s" % (middle_name.upper(), last_name.upper(), first_name)


class Tutor(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    person = models.ForeignKey(Person, null = False)

    def find_by_user(user):
        try:
            person = Person.objects.filter(user=user)
            tutor = Tutor.objects.get(person = person)
            return tutor
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return u"%s" % self.person


class Student(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    registration_id = models.CharField(max_length=10, null=False)
    person          = models.ForeignKey(Person, null=False)


    def __str__(self):
        return u"%s (%s)" % (self.person, self.registration_id)


class Structure(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    acronym = models.CharField(max_length=10, blank=False, null=False)
    title   = models.CharField(max_length=255, blank=False, null=False)
    part_of = models.ForeignKey('self', blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)


class ProgrammeManager(models.Model):
    person  = models.ForeignKey(Person, null=False)
    faculty = models.ForeignKey(Structure, null=False)

    def find_faculty_by_user(user):
        programme_manager = ProgrammeManager.objects.filter(person__user=user).first()
        return programme_manager.faculty

    def __str__(self):
        return u"%s - %s" % (self.person, self.faculty)


class AcademicYear(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    year = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return u"%s-%s" % (self.year, self.year + 1)

    def find_academic_year(id):
        return AcademicYear.objects.get(pk=id)

EVENT_TYPE = (
    ('ACADEMIC_YEAR', 'Academic Year'),
    ('DISSERTATIONS_SUBMISSION_SESS_1', 'Submission of academic dissertations - exam session 1'),
    ('DISSERTATIONS_SUBMISSION_SESS_2', 'Submission of academic dissertations - exam session 2'),
    ('DISSERTATIONS_SUBMISSION_SESS_3', 'Submission of academic dissertations - exam session 3'),
    ('EXAM_SCORES_SUBMISSION_SESS_1', 'Submission of exam scores - exam session 1'),
    ('EXAM_SCORES_SUBMISSION_SESS_2', 'Submission of exam scores - exam session 2'),
    ('EXAM_SCORES_SUBMISSION_SESS_3', 'Submission of exam scores - exam session 3'),
    ('DELIBERATIONS_SESS_1', 'Deliberations - exam session 1'),
    ('DELIBERATIONS_SESS_2', 'Deliberations - exam session 2'),
    ('DELIBERATIONS_SESS_3', 'Deliberations - exam session 3'),
    ('EXAM_SCORES_DIFFUSION_SESS_1', 'Diffusion of exam scores - exam session 1'),
    ('EXAM_SCORES_DIFFUSION_SESS_2', 'Diffusion of exam scores - exam session 2'),
    ('EXAM_SCORES_DIFFUSION_SESS_3', 'Diffusion of exam scores - exam session 3'),
    ('EXAM_ENROLLMENTS_SESS_1', 'Exam enrollments - exam session 1'),
    ('EXAM_ENROLLMENTS_SESS_2', 'Exam enrollments - exam session 2'),
    ('EXAM_ENROLLMENTS_SESS_3', 'Exam enrollments - exam session 3'))

class AcademicCalendar(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    academic_year = models.ForeignKey(AcademicYear, null = False)
    event_type    = models.CharField(max_length = 50, blank = False, null = False, choices = EVENT_TYPE)
    title         = models.CharField(max_length = 50, blank = True, null = True)
    description   = models.TextField(blank = True, null = True)
    start_date    = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)
    end_date      = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)

    def current_academic_year():
        academic_calendar = AcademicCalendar.objects.filter(event_type='ACADEMIC_YEAR').filter(start_date__lte=timezone.now()).filter(end_date__gte=timezone.now()).first()
        return academic_calendar.academic_year

    def find_academic_calendar_by_event_type(academic_year_id, session_number):
        event_type_criteria = "session_exam_"+str(session_number)
        return AcademicCalendar.objects.get(academic_year=academic_year_id, event_type=event_type_criteria)

    def __str__(self):
        return u"%s %s" % (self.academic_year, self.title)


class Offer(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    acronym = models.CharField(max_length = 10,blank = False, null = False)
    title   = models.CharField(max_length = 255, blank = False, null = False)

    def save(self, *args, **kwargs):
        self.acronym = self.acronym.upper()
        super(Offer, self).save(*args, **kwargs)

    @property
    def structure(self):
        return Structure.objects.filter(id=self.id).structure

    def __str__(self):
        return self.acronym


class OfferYear(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    offer         = models.ForeignKey(Offer, null = False)
    academic_year = models.ForeignKey(AcademicYear, null = False)
    acronym       = models.CharField(max_length = 10,blank = False, null = False)
    title         = models.CharField(max_length = 255, blank = False, null = False)
    structure     = models.ForeignKey(Structure, null = True, blank = True)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.offer.acronym)


class OfferEnrollment(models.Model):
    external_id = models.CharField(max_length = 50,blank = True, null = True)
    date_enrollment = models.DateField(auto_now = False, blank = False, null = False, auto_now_add = False)
    offer_year      = models.ForeignKey(OfferYear, null = False)
    student         = models.ForeignKey(Student, null = False)

    def __str__(self):
        return u"%s" % self.student


class OfferYearCalendar(models.Model):
    external_id = models.CharField(max_length = 70,blank = True, null = True)
    academic_calendar = models.ForeignKey(AcademicCalendar, null = False)
    offer_year        = models.ForeignKey(OfferYear, null = True)
    event_type        = models.CharField(max_length = 50, blank = False, null = False, choices = EVENT_TYPE)
    start_date        = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)
    end_date          = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)

    def current_session_exam():
        return OfferYearCalendar.objects.filter(event_type__startswith='session_exam').filter(start_date__lte=timezone.now()).filter(end_date__gte=timezone.now()).first()

    def __str__(self):
        return u"%s" % self.academic_calendar


class LearningUnit(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    acronym     = models.CharField(max_length = 10, blank = False, null = False)
    title       = models.CharField(max_length = 255, null = False)
    description = models.TextField(blank = True, null = True)
    start_year  = models.IntegerField(blank = False, null = False)
    end_year    = models.IntegerField(blank = True, null = True)

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)


class LearningUnitYear(models.Model):
    external_id = models.CharField(max_length = 40,blank = True, null = True)
    acronym       = models.CharField(max_length = 15,blank = False, null = False)
    title         = models.CharField(max_length = 255, blank = False, null = False)
    credits       = models.DecimalField(max_digits = 4, decimal_places = 2, blank = True, null = True)
    academic_year = models.ForeignKey(AcademicYear, null = True)
    learning_unit = models.ForeignKey(LearningUnit, null = True)

    def __str__(self):
        return u"%s - %s" % (self.academic_year,self.learning_unit)


    def find_offer_enrollments(learning_unit_year_id):
        learning_unit_enrollment_list= LearningUnitEnrollment.objects.filter(learning_unit_year=learning_unit_year_id)
        offer_list = []
        for lue in learning_unit_enrollment_list:
            offer_list.append(lue.offer_enrollment)

        return offer_list


class LearningUnitEnrollment(models.Model):
    external_id = models.CharField(max_length = 70,blank = True, null = True)
    date_enrollment    = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)
    learning_unit_year = models.ForeignKey(LearningUnitYear, null = False)
    offer_enrollment   = models.ForeignKey(OfferEnrollment, null = False)

    @property
    def student(self):
        return self.offer_enrollment.student

    @property
    def offer(self):
        return self.offer_enrollment.offer_year

    def __str__(self):
        return u"%s - %s" % (self.learning_unit_year, self.offer_enrollment.student)


class Attribution(models.Model):
    FUNCTION_CHOICES = (
        ('COORDINATOR', _('Coordinator')),
        ('PROFESSOR', _('Professor')))

    external_id = models.CharField(max_length = 40,blank = True, null = True)
    start_date    = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)
    end_date      = models.DateField(auto_now = False, blank = True, null = True, auto_now_add = False)
    function      = models.CharField(max_length = 15, blank = True, null = True,choices = FUNCTION_CHOICES, default = 'UNKNOWN')
    learning_unit = models.ForeignKey(LearningUnit, null = False)
    tutor         = models.ForeignKey(Tutor, null = False)

    def __str__(self):
        return u"%s - %s" % (self.tutor.person, self.function)


class SessionExam(models.Model):
    SESSION_STATUS = (
        ('IDLE', _('Idle')),
        ('OPEN', _('Open')),
        ('CLOSED', _('Closed')))

    external_id = models.CharField(max_length = 40,blank = True, null = True)
    number_session      = models.IntegerField(blank = False, null = False)
    status              = models.CharField(max_length = 10, blank = False, null = False,choices = SESSION_STATUS)
    learning_unit_year  = models.ForeignKey(LearningUnitYear, null = False)
    offer_year_calendar = models.ForeignKey(OfferYearCalendar, blank = False, null = True)

    def current_session_exam():
        offer_calendar = OfferYearCalendar.current_session_exam()
        session_exam = SessionExam.objects.filter(offer_year_calendar=offer_calendar).first()
        return session_exam

    def find_session(id):
        return SessionExam.objects.get(pk=id)

    def find_sessions_by_tutor(tutor, academic_year, session):
        learning_units = Attribution.objects.filter(tutor=tutor).values('learning_unit')
        return SessionExam.objects.filter(number_session=session.number_session
                                 ).filter(learning_unit_year__academic_year=academic_year
                                 ).filter(learning_unit_year__learning_unit__in=learning_units)

    def find_sessions_by_faculty(faculty, academic_year, session):
        return SessionExam.objects.filter(number_session=session.number_session
                                 ).filter(offer_year_calendar__offer_year__academic_year=academic_year
                                 ).filter(offer_year_calendar__offer_year__structure=faculty)

    @property
    def offer(self):
        for rec_exam_enrollment in ExamEnrollment.find_exam_enrollments(self):
            return rec_exam_enrollment.learning_unit_enrollment.offer
        return None

    def __str__(self):
        return u"%s - %d" % (self.learning_unit_year, self.number_session)


class ExamEnrollment(models.Model):
    JUSTIFICATION_TYPES = (
        ('ABSENT',_('Absent')),
        ('CHEATING',_('Cheating')),
        ('ILL',_('Ill')),
        ('JUSTIFIED_ABSENCE',_('Justified absence')),
        ('SCORE_MISSING',_('Score missing')))

    ENCODING_STATUS = (
        ('SAVED',_('Saved')),
        ('SUBMITTED',_('Submitted')))

    external_id = models.CharField(max_length = 70,blank = True, null = True)
    score                    = models.DecimalField(max_digits = 4, decimal_places = 2, blank = True, null = True, validators=[MaxValueValidator(20), MinValueValidator(0)])
    justification            = models.CharField(max_length = 17, blank = True, null = True,choices = JUSTIFICATION_TYPES)
    encoding_status          = models.CharField(max_length = 9, blank = True, null = True,choices = ENCODING_STATUS)
    session_exam             = models.ForeignKey(SessionExam, null = False)
    learning_unit_enrollment = models.ForeignKey(LearningUnitEnrollment, null = False)

    def calculate_progress(enrollments):
        if enrollments:
            progress = len([e for e in enrollments if e.score is not None or e.justification is not None]) / len(enrollments)
            print(progress)
        else:
            progress = 0
        return progress * 100

    def find_exam_enrollments(session_exam):
        enrollments = ExamEnrollment.objects.filter(session_exam=session_exam)
        return enrollments

    def __str__(self):
        return u"%s - %s" % (self.session_exam, self.learning_unit_enrollment)

    def justification_label(self,lang):
        if lang == 'fr':
            if self.justification == "ABSENT":
                return 'Absent'
            if self.justification == "ILL":
                return 'Malade'
            if self.justification == "CHEATING":
                return 'Tricherie'
            if self.justification == "JUSTIFIED_ABSENCE":
                return 'Absence justifiée'
            if self.justification == "SCORE_MISSING":
                return 'Note manquante'
            return None


    def justification_label_authorized(isFac):
        if isFac:
            return '%s, %s, %s, %s, %s' % (_('Absent'), _('Ill'), _('Cheating'), _('Justified absence'), _('Score missing'))
        else:
            return '%s, %s, %s' % (_('Absent'), _('Ill'), _('Cheating'))
