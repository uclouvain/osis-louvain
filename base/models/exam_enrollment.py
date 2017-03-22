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
from decimal import *
from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.core.validators import MaxValueValidator, MinValueValidator
from base.models import person, learning_unit_year, person_address, offer_year_calendar
from attribution.models import attribution
from base.enums import exam_enrollment_justification_type as justification_types
from base.enums import exam_enrollment_state as enrollment_states
import datetime
import unicodedata
from base.models.exceptions import JustificationValueException

JUSTIFICATION_ABSENT_FOR_TUTOR = _('absent')


class ExamEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'enrollment_state', 'session_exam', 'score_draft', 'justification_draft', 'score_final',
                    'justification_final', 'score_reencoded', 'justification_reencoded', 'changed')
    list_filter = ('session_exam__number_session', 'session_exam__learning_unit_year__academic_year')
    fieldsets = ((None, {'fields': ('session_exam', 'enrollment_state', 'learning_unit_enrollment', 'score_draft',
                                    'justification_draft', 'score_final', 'justification_final', 'score_reencoded',
                                    'justification_reencoded')}),)
    raw_id_fields = ('session_exam', 'learning_unit_enrollment')
    search_fields = ['learning_unit_enrollment__offer_enrollment__student__person__first_name',
                     'learning_unit_enrollment__offer_enrollment__student__person__last_name',
                     'learning_unit_enrollment__offer_enrollment__student__registration_id',
                     'learning_unit_enrollment__learning_unit_year__acronym',
                     'session_exam__offer_year_calendar__offer_year__acronym']


class ExamEnrollment(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    score_draft = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(20)])
    score_reencoded = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                          validators=[MinValueValidator(0), MaxValueValidator(20)])
    score_final = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(20)])
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
    return "%s, %s, %s" % (_('absent_pdf_legend'),
                           _('cheating_pdf_legend'),
                           _('score_missing_pdf_legend'))


class ExamEnrollmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('person', 'score_final', 'justification_final', 'modification_date', 'exam_enrollment')
    fieldsets = ((None, {'fields': ('exam_enrollment', 'person', 'score_final', 'justification_final')}),)
    raw_id_fields = ('exam_enrollment', 'person')
    search_fields = ['exam_enrollment__learning_unit_enrollment__offer_enrollment__student__person__first_name',
                     'exam_enrollment__learning_unit_enrollment__offer_enrollment__student__person__last_name',
                     'exam_enrollment__learning_unit_enrollment__offer_enrollment__student__registration_id']
    readonly_fields = ('exam_enrollment', 'person', 'score_final', 'justification_final', 'modification_date')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super(ExamEnrollmentHistoryAdmin, self).get_actions(request)

        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


class ExamEnrollmentHistory(models.Model):
    exam_enrollment = models.ForeignKey(ExamEnrollment)
    person = models.ForeignKey(person.Person)
    score_final = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    justification_final = models.CharField(max_length=20, null=True, choices=justification_types.JUSTIFICATION_TYPES)
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
            tot_progress = tot_progress + progress
            tot_enrollments += len(enrollments)
    return str(tot_progress) + "/" + str(tot_enrollments)


def find_exam_enrollments_by_session_learningunit(session_exm, a_learning_unit_year):
    enrollments = ExamEnrollment.objects.filter(session_exam=session_exm) \
                                        .filter(enrollment_state=enrollment_states.ENROLLED) \
                                        .filter(learning_unit_enrollment__learning_unit_year=a_learning_unit_year)
    return enrollments


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
                             justification=None):
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
    queryset = ExamEnrollment.objects.filter(session_exam__number_session=session_exam_number)
    queryset = queryset.filter(session_exam__offer_year_calendar__start_date__lte=datetime.datetime.now())\
                       .filter(session_exam__offer_year_calendar__end_date__gte=datetime.datetime.now())\
                       .filter(enrollment_state=enrollment_states.ENROLLED)

    if learning_unit_year_id:
        queryset = queryset.filter(learning_unit_enrollment__learning_unit_year_id=learning_unit_year_id)
    elif learning_unit_year_ids:
        queryset = queryset.filter(learning_unit_enrollment__learning_unit_year_id__in=learning_unit_year_ids)

    if tutor:
        # Filter by Tutor is like filter by a list of learningUnits
        # It's not necessary to add a filter if learningUnitYear or learningUnitYearIds are already defined
        if not learning_unit_year_id and not learning_unit_year_ids:
            learning_unit_years = learning_unit_year.find_by_tutor(tutor)
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
        queryset = queryset.filter(justification_final=justification)

    if student_last_name:
        queryset = queryset.filter(
            learning_unit_enrollment__offer_enrollment__student__person__last_name__icontains=student_last_name)

    if student_first_name:
        queryset = queryset.filter(
            learning_unit_enrollment__offer_enrollment__student__person__first_name__icontains=student_first_name)

    return queryset.select_related('learning_unit_enrollment__offer_enrollment__offer_year')\
                   .select_related('learning_unit_enrollment__offer_enrollment__student__person')


def group_by_learning_unit_year_id(exam_enrollments):
    """

    :param exam_enrollments: List of examEnrollments to regroup by earningunitYear.id
    :return: A dictionary where the key is LearningUnitYear.id and the value is a list of examEnrollment
    """
    enrollments_by_learn_unit = {}  # {<learning_unit_year_id> : [<ExamEnrollment>]}
    for exam_enroll in exam_enrollments:
        key = exam_enroll.session_exam.learning_unit_year.id
        if key not in enrollments_by_learn_unit.keys():
            enrollments_by_learn_unit[key] = [exam_enroll]
        else:
            enrollments_by_learn_unit[key].append(exam_enroll)
    return enrollments_by_learn_unit


def scores_sheet_data(exam_enrollments, tutor=None):
    exam_enrollments = sort_for_encodings(exam_enrollments)
    data = {'tutor_global_id': tutor.person.global_id if tutor else ''}
    now = datetime.datetime.now()
    data['publication_date'] = '%s/%s/%s' % (now.day, now.month, now.year)
    data['institution'] = str(_('ucl_denom_location'))
    data['link_to_regulation'] = str(_('link_to_RGEE'))
    data['justification_legend'] = _('justification_legend') % justification_label_authorized()

    # Will contain lists of examEnrollments splitted by learningUnitYear
    enrollments_by_learn_unit = group_by_learning_unit_year_id(exam_enrollments)  # {<learning_unit_year_id> : [<ExamEnrollment>]}

    learning_unit_years = []
    for exam_enrollments in enrollments_by_learn_unit.values():
        # exam_enrollments contains all ExamEnrollment for a learningUnitYear
        learn_unit_year_dict = {}
        # We can take the first element of the list 'exam_enrollments' to get the learning_unit_yr
        # because all exam_enrollments have the same learningUnitYear
        learning_unit_yr = exam_enrollments[0].session_exam.learning_unit_year
        scores_responsible = attribution.find_responsible(learning_unit_yr.id)
        scores_responsible_address = None
        if scores_responsible:
            scores_responsible_address = person_address.find_by_person_label(scores_responsible.person, 'PROFESSIONAL')

        learn_unit_year_dict['academic_year'] = str(learning_unit_yr.academic_year)
        learn_unit_year_dict['scores_responsible'] = {
            'first_name': scores_responsible.person.first_name if scores_responsible else '',
            'last_name': scores_responsible.person.last_name if scores_responsible else ''}

        learn_unit_year_dict['scores_responsible']['address'] = {'location': scores_responsible_address.location
                                                                 if scores_responsible_address else '',
                                                                 'postal_code': scores_responsible_address.postal_code
                                                                 if scores_responsible_address else '',
                                                                 'city': scores_responsible_address.city
                                                                 if scores_responsible_address else ''}
        learn_unit_year_dict['session_number'] = exam_enrollments[0].session_exam.number_session
        learn_unit_year_dict['acronym'] = learning_unit_yr.acronym
        learn_unit_year_dict['title'] = learning_unit_yr.title
        learn_unit_year_dict['decimal_scores'] = learning_unit_yr.decimal_scores

        programs = []

        # Will contain lists of examEnrollments by offerYear (=Program)
        enrollments_by_program = {}  # {<offer_year_id> : [<ExamEnrollment>]}
        for exam_enroll in exam_enrollments:
            key = exam_enroll.learning_unit_enrollment.offer_enrollment.offer_year.id
            if key not in enrollments_by_program.keys():
                enrollments_by_program[key] = [exam_enroll]
            else:
                enrollments_by_program[key].append(exam_enroll)

        for list_enrollments in enrollments_by_program.values():  # exam_enrollments by OfferYear
            exam_enrollment = list_enrollments[0]
            offer_year = exam_enrollment.learning_unit_enrollment.offer_enrollment.offer_year

            deliberation_date = offer_year_calendar.find_deliberation_date(exam_enrollment.session_exam)
            if deliberation_date:
                deliberation_date = deliberation_date.strftime("%d/%m/%Y")
            else:
                deliberation_date = _('not_passed')
            deadline = ""
            if exam_enrollment.session_exam.deadline:
                deadline = exam_enrollment.session_exam.deadline.strftime('%d/%m/%Y')

            program = {'acronym': exam_enrollment.learning_unit_enrollment.offer_enrollment.offer_year.acronym,
                       'deliberation_date': deliberation_date,
                       'deadline': deadline,
                       'address': {'recipient': offer_year.recipient,
                                   'location': offer_year.location,
                                   'postal_code': offer_year.postal_code,
                                   'city': offer_year.city,
                                   'phone': offer_year.phone,
                                   'fax': offer_year.fax,
                                   'email': offer_year.email}}
            enrollments = []
            for exam_enrol in list_enrollments:
                student = exam_enrol.learning_unit_enrollment.student
                score = ''
                if exam_enrol.score_final is not None:
                    if learning_unit_yr.decimal_scores:
                        score = str(exam_enrol.score_final)
                    else:
                        score = str(int(exam_enrol.score_final))
                enrollments.append({
                    "registration_id": student.registration_id,
                    "last_name": student.person.last_name,
                    "first_name": student.person.first_name,
                    "score": score,
                    "justification": _(exam_enrol.justification_final) if exam_enrol.justification_final else ''
                })
            program['enrollments'] = enrollments
            programs.append(program)
            programs = sorted(programs, key=lambda k: k['acronym'])
        learn_unit_year_dict['programs'] = programs
        learning_unit_years.append(learn_unit_year_dict)
    learning_unit_years = sorted(learning_unit_years, key=lambda k: k['acronym'])
    data['learning_unit_years'] = learning_unit_years
    return data


def _normalize_string(string):
    """
    Remove accents in the string passed in parameter.
    For example : 'é - è' ==> 'e - e'  //  'àç' ==> 'ac'
    :param string: The string to normalize.
    :return: The normalized string
    """
    string = string.replace(" ", "")
    return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))


def sort_by_offer_acronym_last_name_first_name(exam_enrollments):
    def _sort(key):
        off_enroll = key.learning_unit_enrollment.offer_enrollment
        last_name = off_enroll.student.person.last_name
        first_name = off_enroll.student.person.first_name
        last_name = _normalize_string(last_name) if last_name else None
        first_name = _normalize_string(first_name) if first_name else None
        offer_year_acronym = key.learning_unit_enrollment.offer_enrollment.offer_year.acronym
        learn_unit_acronym = key.learning_unit_enrollment.learning_unit_year.acronym
        return "%s %s %s %s" % (offer_year_acronym if offer_year_acronym else '',
                                last_name.upper() if last_name else '',
                                first_name.upper() if first_name else '',
                                learn_unit_acronym if learn_unit_acronym else '')

    return sorted(exam_enrollments, key=lambda k: _sort(k))


def sort_for_encodings(exam_enrollments):
    """
    Sort the list by
     0. LearningUnitYear.acronym
     1. offerYear.acronym
     2. student.lastname
     3. sutdent.firstname
    :param exam_enrollments: List of examEnrollments to sort
    :return:
    """

    def _sort(key):
        learn_unit_acronym = key.learning_unit_enrollment.learning_unit_year.acronym
        off_enroll = key.learning_unit_enrollment.offer_enrollment
        acronym = off_enroll.offer_year.acronym
        last_name = off_enroll.student.person.last_name
        first_name = off_enroll.student.person.first_name
        last_name = _normalize_string(last_name) if last_name else None
        first_name = _normalize_string(first_name) if first_name else None
        return "%s %s %s %s" % (learn_unit_acronym if learn_unit_acronym else '',
                                acronym if acronym else '',
                                last_name.upper() if last_name else '',
                                first_name.upper() if first_name else '')

    return sorted(exam_enrollments, key=lambda k: _sort(k))
