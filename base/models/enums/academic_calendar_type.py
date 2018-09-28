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

# TYPES_CATEGORIES
ACADEMIC_CATEGORY = "ACADEMIC"
PROJECT_CATEGORY = "PROJECT"

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

# PROJECT_CALENDAR_TYPES
TESTING = "TESTING"
RELEASE = "RELEASE"
AD_HOC = "AD_HOC"


ACADEMIC_CALENDAR_TYPES = (
    (DELIBERATION, DELIBERATION),
    (DISSERTATION_SUBMISSION, DISSERTATION_SUBMISSION),
    (EXAM_ENROLLMENTS, EXAM_ENROLLMENTS),
    (SCORES_EXAM_DIFFUSION, SCORES_EXAM_DIFFUSION),
    (SCORES_EXAM_SUBMISSION, SCORES_EXAM_SUBMISSION),
    (TEACHING_CHARGE_APPLICATION, TEACHING_CHARGE_APPLICATION),
    (COURSE_ENROLLMENT, COURSE_ENROLLMENT),
    (SUMMARY_COURSE_SUBMISSION, SUMMARY_COURSE_SUBMISSION),
    (EDUCATION_GROUP_EDITION, EDUCATION_GROUP_EDITION),
)

PROJECT_CALENDAR_TYPES = (
    (TESTING, TESTING),
    (RELEASE, RELEASE),
    (AD_HOC, AD_HOC),
)

CALENDAR_TYPES = ACADEMIC_CALENDAR_TYPES + PROJECT_CALENDAR_TYPES

CALENDAR_TYPES_COLORS = {
    DELIBERATION: '#d9534f',
    DISSERTATION_SUBMISSION: '#5bc0de',
    EXAM_ENROLLMENTS: '#5bc0de',
    SCORES_EXAM_DIFFUSION: '#5cb85c',
    SCORES_EXAM_SUBMISSION: '#f0ad4e',
    TEACHING_CHARGE_APPLICATION: '#337ab7'
}
