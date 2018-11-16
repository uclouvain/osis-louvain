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
from django.utils.translation import ugettext_lazy as _

# TYPES_CATEGORIES
ACADEMIC_CATEGORY = "ACADEMIC"
PROJECT_CATEGORY = "PROJECT"
AD_HOC_CATEGORY = "AD_HOC"

# ACADEMIC_CALENDAR_TYPES
DELIBERATION = "DELIBERATION"
DISSERTATION_SUBMISSION = "DISSERTATION_SUBMISSION"
EXAM_ENROLLMENTS = "EXAM_ENROLLMENTS"
SCORES_EXAM_DIFFUSION = "SCORES_EXAM_DIFFUSION"
SCORES_EXAM_SUBMISSION = "SCORES_EXAM_SUBMISSION"
TEACHING_CHARGE_APPLICATION = "TEACHING_CHARGE_APPLICATION"
COURSE_ENROLLMENT = "COURSE_ENROLLMENT"
SUMMARY_COURSE_SUBMISSION = "SUMMARY_COURSE_SUBMISSION"
EDUCATION_GROUP_EDITION = "EDUCATION_GROUP_EDITION"
EDITION_OF_GENERAL_INFORMATION = "EDITION_OF_GENERAL_INFORMATION"

# PROJECT_CALENDAR_TYPES
TESTING = "TESTING"
RELEASE = "RELEASE"


ACADEMIC_CALENDAR_TYPES = (
    (DELIBERATION, _("Deliberation")),
    (DISSERTATION_SUBMISSION, _("Dissertation submission")),
    (EXAM_ENROLLMENTS, _("Exam enrollments")),
    (SCORES_EXAM_DIFFUSION, _("Scores exam diffusion")),
    (SCORES_EXAM_SUBMISSION, _("Scores exam submission")),
    (TEACHING_CHARGE_APPLICATION, _("Teaching charge application")),
    (COURSE_ENROLLMENT, _("Course enrollment")),
    (SUMMARY_COURSE_SUBMISSION, _("Summary course submission")),
    (EDUCATION_GROUP_EDITION, _("Education group edition")),
    (EDITION_OF_GENERAL_INFORMATION, _("Edition of general information")),
)

PROJECT_CALENDAR_TYPES = (
    (TESTING, _("Testing")),
)

AD_HOC_CALENDAR_TYPES = (
    (RELEASE, _("Release")),
)

CALENDAR_TYPES = ACADEMIC_CALENDAR_TYPES + PROJECT_CALENDAR_TYPES + AD_HOC_CALENDAR_TYPES

CALENDAR_TYPES_COLORS = {
    DELIBERATION: '#d9534f',
    DISSERTATION_SUBMISSION: '#5bc0de',
    EXAM_ENROLLMENTS: '#5bc0de',
    SCORES_EXAM_DIFFUSION: '#5cb85c',
    SCORES_EXAM_SUBMISSION: '#f0ad4e',
    TEACHING_CHARGE_APPLICATION: '#337ab7'
}
