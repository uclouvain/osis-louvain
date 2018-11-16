##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import *

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import When, Case, Q, Sum, Count, IntegerField, F
from django.utils.translation import ugettext as _

from attribution.models import attribution
from base.models import person, session_exam_deadline, \
    academic_year as academic_yr, offer_year, program_manager, tutor
from base.models.enums import exam_enrollment_state as enrollment_states, \
    exam_enrollment_justification_type as justification_types
from base.models.exceptions import JustificationValueException
from base.models.utils.admin_extentions import remove_delete_action
from osis_common.models.osis_model_admin import OsisModelAdmin

JUSTIFICATION_ABSENT_FOR_TUTOR = _('Absent')
SCORE_BETWEEN_0_AND_20 = _("Scores must be between 0 and 20")


class ExamEnrollmentAdmin(OsisModelAdmin):
    list_display = ('student', 'enrollment_state', 'session_exam', 'score_draft', 'justification_draft', 'score_final',
                    'justification_final', 'score_reencoded', 'justification_reencoded', 'changed')
    list_filter = ('session_exam__number_session', 'session_exam__learning_unit_year__academic_year')
    raw_id_fields = ('session_exam', 'learning_unit_enrollment')
    search_fields = ['learning_unit_enrollment__offer_enrollment__student__person__first_name',
                     'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                     'learning_unit_enrollment__offer_enrollment__student__registration_id',
                     'learning_unit_enrollment__learning_unit_year__acronym',
                     'learning_unit_enrollment__offer_enrollment__offer_year__acronym']


class ExamEnrollment(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    score_draft = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                      validators=[MinValueValidator(0, message=SCORE_BETWEEN_0_AND_20),
                                                  MaxValueValidator(20, message=SCORE_BETWEEN_0_AND_20)])
    score_reencoded = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                          validators=[MinValueValidator(0,
                                                                        message=SCORE_BETWEEN_0_AND_20),
                                                      MaxValueValidator(20,
                                                                        message=SCORE_BETWEEN_0_AND_20)])
    score_final = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                      validators=[MinValueValidator(0, message=SCORE_BETWEEN_0_AND_20),
                                                  MaxValueValidator(20, message=SCORE_BETWEEN_0_AND_20)])
    justification_draft = models.CharField(max_length=20, blank=True, null=True,
                                           choices=justification_types.JUSTIFICATION_TYPES)
    justification_reencoded = models.CharField(max_length=20, blank=True, null=True,
                                               choices=justification_types.JUSTIFICATION_TYPES)
    justification_final = models.CharField(max_length=20, blank=True, null=True,
                                           choices=justification_types.JUSTIFICATION_TYPES)
    session_exam = models.ForeignKey('SessionExam')
    learning_unit_enrollment = models.ForeignKey('LearningUnitEnrollment')
    enrollment_state = models.CharField(max_length=20,
                                        default=enrollment_states.ENROLLED,
                                        choices=enrollment_states.STATES,
                                        db_index=True)

    def student(self):
        return self.learning_unit_enrollment.student

    def justification_valid(self):
        valid_justifs = [j[0] for j in justification_types.JUSTIFICATION_TYPES]
        if self.justification_draft:
            if self.justification_draft not in valid_justifs:
                return False
        if self.justification_reencoded:
            if self.justification_reencoded not in valid_justifs:
                return False
        if self.justification_final:
            if self.justification_final not in valid_justifs:
                return False
        return True

    def save(self, *args, **kwargs):
        if not self.justification_valid():
            raise JustificationValueException
        super(ExamEnrollment, self).save(*args, **kwargs)

    def __str__(self):
        return u"%s - %s" % (self.session_exam, self.learning_unit_enrollment)

    @property
    def is_final(self):
        return self.score_final is not None or self.justification_final

    @property
    def is_draft(self):
        return self.score_draft is not None or self.justification_draft

    @property
    def is_score_missing_as_program_manager(self):
        return not self.is_final

    @property
    def to_validate_by_program_manager(self):
        sc_reencoded = None
        if self.score_reencoded is not None:
            sc_reencoded = Decimal('%.2f' % self.score_reencoded)

        return self.score_final != sc_reencoded or self.justification_final != self.justification_reencoded

    @property
    def to_validate_by_tutor(self):
        sc_reencoded = None
        if self.score_reencoded is not None:
            sc_reencoded = Decimal('%.2f' % self.score_reencoded)

        return self.score_draft != sc_reencoded or self.justification_draft != self.justification_reencoded

    @property
    def justification_draft_display(self):
        if is_absence_justification(self.justification_draft):
            return JUSTIFICATION_ABSENT_FOR_TUTOR
        elif self.justification_draft:
            return _(self.justification_draft)
        else:
            return None

    @property
    def justification_final_display_as_tutor(self):
        if is_absence_justification(self.justification_final):
            return JUSTIFICATION_ABSENT_FOR_TUTOR
        elif self.justification_final:
            return _(self.justification_final)
        else:
            return None

    @property
    def justification_reencoded_display_as_tutor(self):
        if is_absence_justification(self.justification_reencoded):
            return JUSTIFICATION_ABSENT_FOR_TUTOR
        elif self.justification_reencoded:
            return _(self.justification_reencoded)
        else:
            return None

    @property
    def is_score_missing_as_tutor(self):
        return not self.is_final and not self.is_draft


def find_by_ids(ids):
    return ExamEnrollment.objects.filter(pk__in=ids)


def get_session_exam_deadline(enrollment):
    if hasattr(enrollment.learning_unit_enrollment.offer_enrollment, 'session_exam_deadlines') and \
            enrollment.learning_unit_enrollment.offer_enrollment.session_exam_deadlines:
        # Prefetch related
        return enrollment.learning_unit_enrollment.offer_enrollment.session_exam_deadlines[0]
    else:
        # No prefetch
        offer_enrollment = enrollment.learning_unit_enrollment.offer_enrollment
        nb_session = enrollment.session_exam.number_session
        return session_exam_deadline.get_by_offer_enrollment_nb_session(offer_enrollment, nb_session)


def is_deadline_reached(enrollment):
    exam_deadline = get_session_exam_deadline(enrollment)
    if exam_deadline:
        return exam_deadline.is_deadline_reached
    return False


def is_deadline_tutor_reached(enrollment):
    exam_deadline = get_session_exam_deadline(enrollment)
    if exam_deadline:
        return exam_deadline.is_deadline_tutor_reached
    return False


def get_deadline(enrollment):
    exam_deadline = get_session_exam_deadline(enrollment)
    if exam_deadline:
        return exam_deadline.deadline_tutor_computed if exam_deadline.deadline_tutor_computed else \
            exam_deadline.deadline
    return None


def is_absence_justification(justification):
    return justification in [justification_types.ABSENCE_UNJUSTIFIED, justification_types.ABSENCE_JUSTIFIED]


def calculate_exam_enrollment_progress(enrollments):
    if enrollments:
        progress = len([e for e in enrollments if e.score_final is not None or e.justification_final]) / len(
            enrollments)
    else:
        progress = 0
    return progress * 100


def justification_label_authorized():
    return "%s, %s" % (_('A=Absent'),
                       _('T=Cheating'))


class ExamEnrollmentHistoryAdmin(OsisModelAdmin):
    list_display = ('person', 'score_final', 'justification_final', 'modification_date', 'exam_enrollment')
    raw_id_fields = ('exam_enrollment', 'person')
    search_fields = ['exam_enrollment__learning_unit_enrollment__offer_enrollment__student__person__first_name',
                     'exam_enrollment__learning_unit_enrollment__offer_enrollment__student__person__last_name',
                     'exam_enrollment__learning_unit_enrollment__offer_enrollment__student__registration_id',
                     'exam_enrollment__learning_unit_enrollment__learning_unit_year__acronym']
    list_filter = ('exam_enrollment__learning_unit_enrollment__learning_unit_year__academic_year',)
    readonly_fields = ('exam_enrollment', 'person', 'score_final', 'justification_final', 'modification_date')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        return remove_delete_action(super(ExamEnrollmentHistoryAdmin, self).get_actions(request))


class ExamEnrollmentHistory(models.Model):
    exam_enrollment = models.ForeignKey(ExamEnrollment)
    person = models.ForeignKey(person.Person)
    score_final = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    justification_final = models.CharField(max_length=20, null=True, choices=justification_types.JUSTIFICATION_TYPES)
    modification_date = models.DateTimeField(auto_now=True)


def create_exam_enrollment_historic(user, enrollment):
    exam_enrollment_history = ExamEnrollmentHistory()
    exam_enrollment_history.exam_enrollment = enrollment
    exam_enrollment_history.score_final = enrollment.score_final
    exam_enrollment_history.justification_final = enrollment.justification_final
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
            tot_progress = tot_progress + progress
            tot_enrollments += len(enrollments)
    return str(tot_progress) + "/" + str(tot_enrollments)


def find_exam_enrollments_by_session_learningunit(session_exm, a_learning_unit_year):
    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
        .filter(enrollment_state=enrollment_states.ENROLLED) \
        .filter(learning_unit_enrollment__learning_unit_year=a_learning_unit_year)
    return enrollments


def get_progress_by_learning_unit_years_and_offer_years(user,
                                                        session_exam_number,
                                                        learning_unit_year_id=None,
                                                        learning_unit_year_ids=None,
                                                        offer_year_id=None,
                                                        academic_year=None):
    if offer_year_id:
        offer_year_ids = [offer_year_id]
    else:
        offer_year_ids = offer_year.find_by_user(user).values_list('id', flat=True)

    tutor_user = None
    if not program_manager.is_program_manager(user):
        tutor_user = tutor.find_by_user(user)

    queryset = find_for_score_encodings(session_exam_number=session_exam_number,
                                        learning_unit_year_id=learning_unit_year_id,
                                        learning_unit_year_ids=learning_unit_year_ids,
                                        offers_year=offer_year_ids,
                                        tutor=tutor_user,
                                        academic_year=academic_year,
                                        with_session_exam_deadline=False)

    return queryset.values('session_exam', 'learning_unit_enrollment__learning_unit_year',
                           'learning_unit_enrollment__offer_enrollment__offer_year') \
        .annotate(
        total_exam_enrollments=Count('id'),
        learning_unit_enrollment__learning_unit_year__acronym=
        F('learning_unit_enrollment__learning_unit_year__acronym'),
        learning_unit_enrollment__learning_unit_year__specific_title=
        F('learning_unit_enrollment__learning_unit_year__specific_title'),
        learning_unit_enrollment__learning_unit_year__learning_container_year__common_title=
        F('learning_unit_enrollment__learning_unit_year__learning_container_year__common_title'),
        exam_enrollments_encoded=Sum(Case(
            When(Q(score_final__isnull=False) | Q(justification_final__isnull=False), then=1),
            default=0,
            output_field=IntegerField())
        ),
        scores_not_yet_submitted=Sum(Case(
            When((Q(score_draft__isnull=False) &
                  Q(score_final__isnull=True) &
                  Q(justification_final__isnull=True)) | (Q(justification_draft__isnull=False) &
                                                          Q(score_final__isnull=True) &
                                                          Q(justification_final__isnull=True))
                 , then=1),
            default=0,
            output_field=IntegerField()))
    )


def find_for_score_encodings(session_exam_number,
                             learning_unit_year_id=None,
                             learning_unit_year_ids=None,
                             tutor=None,
                             offer_year_id=None,
                             offers_year=None,
                             with_justification_or_score_final=False,
                             with_justification_or_score_draft=False,
                             registration_id=None,
                             student_last_name=None,
                             student_first_name=None,
                             justification=None,
                             academic_year=None,
                             with_session_exam_deadline=True):
    """
    :param session_exam_number: Integer represents the number_session of the Session_exam (1,2,3,4 or 5). It's
                                a mandatory field to not confuse exam scores from different sessions.
    :param learning_unit_year_id: Filter OfferEnrollments by learning_unit_year.
    :param learning_unit_year_ids: Filter OfferEnrollments by a list of learning_unit_year.
    :param tutor: Filter OfferEnrollments by Tutor.
    :param offer_year_id: Filter OfferEnrollments by Offer year ids
    :param offers_year: Filter OfferEnrollments by OfferYear.
    :param with_justification_or_score_final: If True, only examEnrollments with a score_final or a justification_final
                                              are returned.
    :param with_justification_or_score_draft: If True, only examEnrollments with a score_draft or a justification_draft
                                              are returned.
    :return: All filtered examEnrollments.
    """
    if not academic_year:
        academic_year = academic_yr.current_academic_year()

    queryset = ExamEnrollment.objects.filter(session_exam__number_session=session_exam_number,
                                             learning_unit_enrollment__learning_unit_year__academic_year=academic_year,
                                             enrollment_state=enrollment_states.ENROLLED)
    if learning_unit_year_id:
        queryset = queryset.filter(learning_unit_enrollment__learning_unit_year_id=learning_unit_year_id)
    elif learning_unit_year_ids is not None:
        queryset = queryset.filter(learning_unit_enrollment__learning_unit_year_id__in=learning_unit_year_ids)

    if tutor:
        # Filter by Tutor is like filter by a list of learningUnits
        # It's not necessary to add a filter if learningUnitYear or learningUnitYearIds are already defined
        if not learning_unit_year_id and not learning_unit_year_ids:
            learning_unit_years = attribution.find_by_tutor(tutor)
            queryset = queryset.filter(learning_unit_enrollment__learning_unit_year_id__in=learning_unit_years)

    if offer_year_id:
        queryset = queryset.filter(learning_unit_enrollment__offer_enrollment__offer_year_id=offer_year_id)
    elif offers_year:
        queryset = queryset.filter(learning_unit_enrollment__offer_enrollment__offer_year_id__in=offers_year)

    if with_justification_or_score_final:
        queryset = queryset.exclude(score_final=None, justification_final=None)

    if with_justification_or_score_draft:
        queryset = queryset.exclude(score_draft=None, justification_draft=None)

    if registration_id:
        queryset = queryset.filter(learning_unit_enrollment__offer_enrollment__student__registration_id=registration_id)

    if justification:
        if justification == justification_types.SCORE_MISSING:
            # Show only empty values
            queryset = queryset.filter(justification_final__isnull=True,
                                       score_final__isnull=True)
        else:
            queryset = queryset.filter(justification_final=justification)

    if student_last_name:
        queryset = queryset.filter(
            learning_unit_enrollment__offer_enrollment__student__person__last_name__icontains=student_last_name)

    if student_first_name:
        queryset = queryset.filter(
            learning_unit_enrollment__offer_enrollment__student__person__first_name__icontains=student_first_name)

    if with_session_exam_deadline:
        queryset = queryset.prefetch_related(
            models.Prefetch('learning_unit_enrollment__offer_enrollment__sessionexamdeadline_set',
                            queryset=session_exam_deadline.filter_by_nb_session(session_exam_number),
                            to_attr="session_exam_deadlines")
        )

    return queryset.select_related('learning_unit_enrollment__offer_enrollment__offer_year') \
        .select_related('session_exam') \
        .select_related('learning_unit_enrollment__offer_enrollment__student__person') \
        .select_related('learning_unit_enrollment__learning_unit_year')


def find_by_student(a_student):
    return ExamEnrollment.objects.filter(learning_unit_enrollment__offer_enrollment__student=a_student) \
        .order_by('-learning_unit_enrollment__learning_unit_year__academic_year__year',
                  'session_exam__number_session',
                  'learning_unit_enrollment__learning_unit_year__acronym')
