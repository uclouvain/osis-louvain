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
from django.utils.translation import gettext_lazy as _

# TYPES_CATEGORIES
from base.models.utils.utils import ChoiceEnum

ACADEMIC_CATEGORY = "ACADEMIC"

# ACADEMIC_CALENDAR_TYPES
DELIBERATION = "DELIBERATION"
DISSERTATION_SUBMISSION = "DISSERTATION_SUBMISSION"
EXAM_ENROLLMENTS = "EXAM_ENROLLMENTS"
SCORES_EXAM_DIFFUSION = "SCORES_EXAM_DIFFUSION"
SCORES_EXAM_SUBMISSION = "SCORES_EXAM_SUBMISSION"
TEACHING_CHARGE_APPLICATION = "TEACHING_CHARGE_APPLICATION"
COURSE_ENROLLMENT = "COURSE_ENROLLMENT"
SUMMARY_COURSE_SUBMISSION = "SUMMARY_COURSE_SUBMISSION"
SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE = "SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE"
EDUCATION_GROUP_EDITION = "EDUCATION_GROUP_EDITION"
EDUCATION_GROUP_SWITCH = "EDUCATION_GROUP_SWITCH"
EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT = "EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT"
EDUCATION_GROUP_LIMITED_DAILY_MANAGEMENT = "EDUCATION_GROUP_LIMITED_DAILY_MANAGEMENT"
LEARNING_UNIT_EXTENDED_PROPOSAL_MANAGEMENT = "LEARNING_UNIT_EXTENDED_PROPOSAL_MANAGEMENT"
LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT = "LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT"

ACADEMIC_CALENDAR_TYPES = (
    (DELIBERATION, _("Deliberation")),
    (DISSERTATION_SUBMISSION, _("Dissertation submission")),
    (EXAM_ENROLLMENTS, _("Exam enrollments")),
    (SCORES_EXAM_DIFFUSION, _("Scores diffusion")),
    (SCORES_EXAM_SUBMISSION, _("Scores exam submission")),
    (TEACHING_CHARGE_APPLICATION, _("Application for vacant courses")),
    (COURSE_ENROLLMENT, _("Course enrollment")),
    (SUMMARY_COURSE_SUBMISSION, _("Summary course submission")),
    (SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE, _("Summary course submission force majeure")),
    (EDUCATION_GROUP_SWITCH, _("Education group switch")),
    (EDUCATION_GROUP_EDITION, _("Education group edition")),
    (EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT, _("Education group extended daily management")),
    (EDUCATION_GROUP_LIMITED_DAILY_MANAGEMENT, _("Education group limited daily management")),
    (LEARNING_UNIT_EXTENDED_PROPOSAL_MANAGEMENT, _("Extended proposal management")),
    (LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT, _("Limited proposal management")),
)


class AcademicCalendarTypes(ChoiceEnum):
    DELIBERATION = _("Deliberation")
    DISSERTATION_SUBMISSION = _("Dissertation submission")
    EXAM_ENROLLMENTS = _("Exam enrollments")
    SCORES_EXAM_DIFFUSION = _("Scores diffusion")
    SCORES_EXAM_SUBMISSION = _("Scores exam submission")
    TEACHING_CHARGE_APPLICATION = _("Application for vacant courses")
    ACCESS_SCHEDULE_CALENDAR = _("Access schedule calendar")
    COURSE_ENROLLMENT = _("Course enrollment")
    SUMMARY_COURSE_SUBMISSION = _("Summary course submission")
    SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE = _("Summary course submission force majeure")
    EDUCATION_GROUP_SWITCH = _("Education group switch")
    EDUCATION_GROUP_EDITION = _("Education group edition")
    EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT = _("Education group extended daily management")
    EDUCATION_GROUP_LIMITED_DAILY_MANAGEMENT = _("Education group limited daily management")
    LEARNING_UNIT_EXTENDED_PROPOSAL_MANAGEMENT = _("Extended proposal management")
    LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT = _("Limited proposal management")


CALENDAR_TYPES_COLORS = {
    DELIBERATION: '#d9534f',
    DISSERTATION_SUBMISSION: '#5bc0de',
    EXAM_ENROLLMENTS: '#5bc0de',
    SCORES_EXAM_DIFFUSION: '#5cb85c',
    SCORES_EXAM_SUBMISSION: '#f0ad4e',
    TEACHING_CHARGE_APPLICATION: '#337ab7'
}
