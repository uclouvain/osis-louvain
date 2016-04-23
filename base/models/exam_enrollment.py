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
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from base.models import person
from django.utils import timezone


JUSTIFICATION_TYPES = (
    ('ABSENT', _('absent')),
    ('CHEATING', _('cheating')),
    ('ILL', _('ill')),
    ('JUSTIFIED_ABSENCE', _('justified_absence')),
    ('SCORE_MISSING', _('score_missing')))


class ExamEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'session_exam', 'score_final', 'justification_final', 'encoding_status', 'changed')
    list_filter = ('encoding_status', 'session_exam__number_session')
    fieldsets = ((None, {'fields': ('session_exam','learning_unit_enrollment','score_draft','justification_draft',
                                    'score_final','justification_final')}),)
    raw_id_fields = ('session_exam', 'learning_unit_enrollment')
    search_fields = ['learning_unit_enrollment__offer_enrollment__student__person__first_name',
                     'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                     'learning_unit_enrollment__offer_enrollment__student__registration_id',
                     'learning_unit_enrollment__learning_unit_year__acronym']


class ExamEnrollment(models.Model):
    ENCODING_STATUS_LIST = (
        ('SAVED', _('saved')),
        ('SUBMITTED', _('submitted')))

    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    score_draft = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    score_reencoded = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    score_final = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    justification_draft = models.CharField(max_length=20, blank=True, null=True, choices=JUSTIFICATION_TYPES)
    justification_reencoded = models.CharField(max_length=20, blank=True, null=True, choices=JUSTIFICATION_TYPES)
    justification_final = models.CharField(max_length=20, blank=True, null=True, choices=JUSTIFICATION_TYPES)
    encoding_status = models.CharField(max_length=9, blank=True, null=True, choices=ENCODING_STATUS_LIST)
    session_exam = models.ForeignKey('SessionExam')
    learning_unit_enrollment = models.ForeignKey('LearningUnitEnrollment')

    def student(self):
        return self.learning_unit_enrollment.student

    def __str__(self):
        return u"%s - %s" % (self.session_exam, self.learning_unit_enrollment)


def find_exam_enrollments_by_session(session_exm):
    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
        .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                  'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                  'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrollments


def find_exam_enrollments_drafts_by_session(session_exam):
    """ Return the enrollments of a session but not the ones already submitted. """
    enrolls = ExamEnrollment.objects.filter(session_exam=session_exam) \
                                    .filter(score_final__isnull=True) \
                                    .filter(models.Q(justification_final__isnull=True) |
                                            models.Q(justification_final='')) \
                                    .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                                              'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                                              'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrolls


def find_exam_enrollments_to_validate_by_session(session_exam):
    enrolls = ExamEnrollment.objects.filter(session_exam=session_exam) \
                                    .filter(~models.Q(score_draft=models.F('score_reencoded')) |
                                            ~models.Q(justification_draft=models.F('justification_reencoded'))) \
                                    .filter(score_final__isnull=True) \
                                    .filter(models.Q(justification_final__isnull=True) |
                                            models.Q(justification_final='')) \
                                    .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                                              'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                                              'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrolls


def find_by_enrollment_session(learning_unit_enrollment, session_exam_number_session):
    return ExamEnrollment.objects.filter(learning_unit_enrollment=learning_unit_enrollment) \
                                 .filter(session_exam__number_session=session_exam_number_session).first()


def count_encoded_scores(enrollments):
    """ Count the scores that were already encoded but not submitted yet. """
    counter = 0
    for enrollment in enrollments:
        if (enrollment.score_draft or enrollment.justification_draft) \
                and not enrollment.score_final \
                and not enrollment.justification_final:
            counter += 1

    return counter


def calculate_exam_enrollment_progress(enrollments):
    if enrollments:
        progress = len([e for e in enrollments if e.score_final or e.justification_final]) / len(enrollments)
    else:
        progress = 0
    return progress * 100


def calculate_session_exam_progress(session_exam):
    enrollments = list(find_exam_enrollments_by_session(session_exam))

    if enrollments:
        progress = 0
        for e in enrollments:
            if e.score_final is not None or e.justification_final is not None:
                progress += 1
        return str(progress) + "/" + str(len(enrollments))
    else:
        return "0/0"


def justification_label_authorized(is_fac):
    if is_fac:
        return '%s, %s, %s, %s, %s' % (_('absent'),
                                       _('cheating'),
                                       _('ill'),
                                       _('justified_absence'),
                                       _('score_missing'))
    else:
        return '%s, %s, %s' % (_('absent'),
                               _('cheating'),
                               _('score_missing'))


class ExamEnrollmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('exam_enrollment', 'person', 'score_final', 'justification_final', 'modification_date')
    fieldsets = ((None, {'fields': ('exam_enrollment', 'person', 'score_final', 'justification_final')}),)


class ExamEnrollmentHistory(models.Model):
    exam_enrollment = models.ForeignKey(ExamEnrollment)
    person = models.ForeignKey(person.Person)
    score_final = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    justification_final = models.CharField(max_length=20, null=True, choices=JUSTIFICATION_TYPES)
    modification_date = models.DateTimeField(auto_now=True)


def create_exam_enrollment_historic(user, enrollment, score, justification):
    exam_enrollment_history = ExamEnrollmentHistory()
    exam_enrollment_history.exam_enrollment = enrollment
    exam_enrollment_history.score_final = score
    exam_enrollment_history.justification_final = justification
    exam_enrollment_history.person = person.find_by_user(user)
    exam_enrollment_history.save()


def get_progress(session_exm_list, learning_unt):
    tot_progress = 0
    tot_enrollments = 0
    for session_exm in session_exm_list:
        enrollments = list(find_exam_enrollments_by_session_learningunit(session_exm, learning_unt))
        if enrollments:
            progress = 0
            for e in enrollments:
                if e.score_final is not None or e.justification_final is not None:
                    progress += 1
            tot_progress = tot_progress+progress
            tot_enrollments += len(enrollments)
    return str(tot_progress)+"/"+str(tot_enrollments)


def find_exam_enrollments_by_session_learningunit(session_exm, learning_unt):
    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
        .filter(learning_unit_enrollment__learning_unit_year__learning_unit=learning_unt)
    return enrollments


def find_exam_enrollments_by_session_structure(session_exm, structure):
    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
        .filter(learning_unit_enrollment__offer_enrollment__offer_year__structure=structure) \
        .filter(session_exam__offer_year_calendar__start_date__lte=timezone.now()) \
        .filter(session_exam__offer_year_calendar__end_date__gte=timezone.now())\
        .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                  'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                  'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrollments


def find_exam_enrollments_by_session_pgm(session_exm,program_mgr_list):
    offer_year_structures = []
    for p in program_mgr_list:
        if p.offer_year.structure not in offer_year_structures:
            offer_year_structures.append(p.offer_year.structure)

    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
                .filter(learning_unit_enrollment__offer_enrollment__offer_year__structure__in=offer_year_structures)\
                .filter(session_exam__offer_year_calendar__start_date__lte=timezone.now()) \
                .filter(session_exam__offer_year_calendar__end_date__gte=timezone.now())\
                .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                          'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                          'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrollments


def find_exam_enrollments_drafts_existing_by_session(session_exam):
    """ Return the enrollments of a session but not the ones already submitted. """
    enrolls = ExamEnrollment.objects.filter(session_exam=session_exam) \
                                    .filter(score_final__isnull=True) \
                                    .filter(models.Q(justification_draft__isnull=False) |
                                            models.Q(score_draft__isnull=False)) \
                                    .filter(models.Q(justification_final__isnull=True) |
                                            models.Q(justification_final='')) \
                                    .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                                              'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                                              'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrolls


def find_exam_enrollments_drafts_existing_pgmer_by_session(session_exam):
    """ Return the enrollments of a session but not the ones already submitted. """
    enrolls = ExamEnrollment.objects.filter(session_exam=session_exam) \
                                    .filter(models.Q(justification_draft__isnull=False) |
                                            models.Q(score_draft__isnull=False)) \
                                    .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                                              'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                                              'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrolls


def find_exam_enrollments_double_pgmer_by_session(session_exam):
    """ Return the enrollments of a session but not the ones already submitted. """
    enrolls = ExamEnrollment.objects.filter(session_exam=session_exam) \
                                    .filter(models.Q(justification_draft__isnull=False) |
                                            models.Q(score_draft__isnull=False)) \
                                    .filter(models.Q(justification_reencoded__isnull=False) |
                                            models.Q(score_reencoded__isnull=False)) \
                                    .order_by('learning_unit_enrollment__offer_enrollment__offer_year__acronym',
                                              'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                                              'learning_unit_enrollment__offer_enrollment__student__person__first_name')
    return enrolls
