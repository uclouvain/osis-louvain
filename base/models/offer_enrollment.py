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
from django.db import models

from base.models.enums import offer_enrollment_state
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class OfferEnrollmentAdmin(SerializableModelAdmin):
    list_display = ('offer_year', 'education_group_year', 'student', 'date_enrollment', 'enrollment_state', 'changed')
    list_filter = ('offer_year__academic_year', 'enrollment_state')
    search_fields = ['offer_year__acronym', 'education_group_year__acronym', 'student__person__first_name',
                     'student__person__last_name', 'student__registration_id', 'enrollment_state']


class OfferEnrollment(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    date_enrollment = models.DateField()
    offer_year = models.ForeignKey('OfferYear', on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.PROTECT)
    enrollment_state = models.CharField(max_length=15, choices=offer_enrollment_state.STATES, blank=True, null=True)
    education_group_year = models.ForeignKey('EducationGroupYear', null=True, on_delete=models.PROTECT)

    def __str__(self):
        return u"%s - %s" % (self.student, self.offer_year)

    class Meta:
        permissions = (
            ("can_access_student_path", "Can access student path"),
            ("can_access_evaluation", "Can access evaluation"),
        )
