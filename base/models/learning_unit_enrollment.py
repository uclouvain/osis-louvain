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

from base.models.enums import learning_unit_enrollment_state
from osis_common.models.serializable_model import SerializableModelAdmin, SerializableModel


class LearningUnitEnrollmentAdmin(SerializableModelAdmin):
    list_display = ('student', 'learning_unit_year', 'offer', 'date_enrollment', 'enrollment_state', 'changed')
    list_filter = ('learning_unit_year__academic_year', 'enrollment_state',)
    search_fields = ['learning_unit_year__acronym',
                     'offer_enrollment__offer_year__acronym',
                     'offer_enrollment__student__registration_id',
                     'offer_enrollment__student__person__first_name',
                     'offer_enrollment__student__person__last_name']


class LearningUnitEnrollment(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    date_enrollment = models.DateField()
    learning_unit_year = models.ForeignKey('LearningUnitYear', on_delete=models.CASCADE)
    offer_enrollment = models.ForeignKey('OfferEnrollment', on_delete=models.PROTECT)
    enrollment_state = models.CharField(max_length=20, choices=learning_unit_enrollment_state.STATES, default="")

    class Meta:
        unique_together = ('offer_enrollment', 'learning_unit_year', 'enrollment_state',)

    @property
    def student(self):
        return self.offer_enrollment.student

    @property
    def offer(self):
        return self.offer_enrollment.offer_year

    def __str__(self):
        return u"%s - %s" % (self.learning_unit_year, self.offer_enrollment.student)


def find_by_learning_unit_year(a_learning_unit_year):
    return LearningUnitEnrollment.objects.filter(learning_unit_year=a_learning_unit_year)
