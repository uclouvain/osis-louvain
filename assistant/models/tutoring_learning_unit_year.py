##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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


class TutoringLearningUnitYear(models.Model):
    mandate = models.ForeignKey('AssistantMandate')
    learning_unit_year = models.ForeignKey('base.LearningUnitYear')
    sessions_duration = models.PositiveIntegerField(null=True, blank=True)
    sessions_number = models.PositiveIntegerField(null=True, blank=True)
    series_number = models.PositiveIntegerField(null=True, blank=True)
    face_to_face_duration = models.PositiveIntegerField(null=True, blank=True)
    attendees = models.PositiveIntegerField(null=True, blank=True)
    preparation_duration = models.PositiveIntegerField(null=True, blank=True)
    exams_supervision_duration = models.PositiveIntegerField(null=True, blank=True)
    others_delivery = models.TextField(null=True, blank=True)


def find_by_id(tutoring_learning_unit_id):
    return TutoringLearningUnitYear.objects.get(id=tutoring_learning_unit_id)


def find_for_mandate_for_academic_year(mandate, academic_year):
    return TutoringLearningUnitYear.objects.filter(mandate=mandate, learning_unit_year__academic_year=academic_year)


def find_by_mandate(mandate):
    return TutoringLearningUnitYear.objects.filter(mandate=mandate).order_by('learning_unit_year__academic_year')


def find_by_mandate_and_learning_unit(mandate, learning_unit):
    return TutoringLearningUnitYear.objects.filter(mandate=mandate).\
        filter(learning_unit_year=learning_unit)
