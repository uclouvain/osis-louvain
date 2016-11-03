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
from base.enums import exam_enrollment_state
from base.models import academic_year


class ScoresEncodingAdmin(admin.ModelAdmin):
    list_display = ('pgm_manager_person',
                    'offer_year',
                    'learning_unit_year',
                    'total_exam_enrollments',
                    'exam_enrollments_encoded')
    search_fields = ['pgm_manager_person__last_name', 'pgm_manager_person__first_name']


# Mapping of a view.
class ScoresEncoding(models.Model):
    id = models.BigIntegerField(primary_key=True)
    program_manager = models.ForeignKey('ProgramManager', on_delete=models.DO_NOTHING)
    pgm_manager_person = models.ForeignKey('Person', related_name='pgm_manager_person', on_delete=models.DO_NOTHING)
    offer_year = models.ForeignKey('OfferYear', on_delete=models.DO_NOTHING)
    learning_unit_year = models.ForeignKey('LearningUnitYear', on_delete=models.DO_NOTHING)
    total_exam_enrollments = models.IntegerField()
    exam_enrollments_encoded = models.IntegerField()
    enrollment_state = models.CharField(max_length=20,
                                        default=exam_enrollment_state.ENROLLED,
                                        choices=exam_enrollment_state.STATES)

    class Meta:
        managed = False
        db_table = 'app_scores_encoding'

        permissions = (
            ("can_access_scoreencoding", "Can access scoreencoding"),
        )


def search(user, learning_unit_year_id=None, offer_year_id=None, learning_unit_year_ids=None):
    queryset = ScoresEncoding.objects.filter(enrollment_state=exam_enrollment_state.ENROLLED) \
                                     .filter(offer_year__academic_year=academic_year.current_academic_year()) \
                                     .filter(learning_unit_year__academic_year=academic_year.current_academic_year())

    if offer_year_id:
        queryset = queryset.filter(offer_year_id=offer_year_id)

    if learning_unit_year_id:
        queryset = queryset.filter(learning_unit_year_id=learning_unit_year_id)
    elif learning_unit_year_ids:
        queryset = queryset.filter(learning_unit_year_id__in=learning_unit_year_ids)

    return queryset.filter(pgm_manager_person__user=user)

