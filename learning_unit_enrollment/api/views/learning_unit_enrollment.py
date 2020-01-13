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
from rest_framework import generics

from backoffice.settings.rest_framework.pagination import LimitOffsetPaginationForEnrollments
from base.models.learning_unit_enrollment import LearningUnitEnrollment
from django_filters import rest_framework as filters

from learning_unit_enrollment.api.serializers.learning_unit_enrollment import LearningUnitEnrollmentSerializer


class CharListFilter(filters.CharFilter):
    def filter(self, qs, value):
        self.lookup_expr = 'in'
        values = value.split(u',')
        return super(CharListFilter, self).filter(qs, values)


class LearningUnitEnrollmentFilter(filters.FilterSet):
    offer_acronym = filters.CharFilter(
        field_name="offer_enrollment__education_group_year__acronym",
        lookup_expr='icontains'
    )
    year = filters.NumberFilter(field_name="learning_unit_year__academic_year__year")
    learning_unit_enrollment_state = filters.CharFilter(field_name="enrollment_state")
    offer_enrollment_state = CharListFilter(field_name="offer_enrollment__enrollment_state")

    class Meta:
        model = LearningUnitEnrollment
        fields = [
            'offer_acronym',
            'year',
            'learning_unit_enrollment_state',
            'offer_enrollment_state',
        ]


class LearningUnitEnrollmentList(generics.ListAPIView):
    """
       Return a list of all the training with optional filtering.
    """

    pagination_class = LimitOffsetPaginationForEnrollments  # TODO :: remove this when xls will be produced in Osis

    queryset = LearningUnitEnrollment.objects.select_related(
        'offer_enrollment__student__person',
        'learning_unit_year__academic_year',
        'offer_enrollment__education_group_year__education_group_type',
    )

    serializer_class = LearningUnitEnrollmentSerializer
    filter_class = LearningUnitEnrollmentFilter

    ordering = (
        'learning_unit_year__acronym',
        'learning_unit_year__academic_year__year',
    )


class EnrollmentsByStudent(LearningUnitEnrollmentList):
    name = 'enrollments-list-by-student'

    def get_queryset(self):
        return super().get_queryset().filter(offer_enrollment__student__registration_id=self.kwargs['registration_id'])


class EnrollmentsByLearningUnit(LearningUnitEnrollmentList):
    name = 'enrollments-list-by-learning-unit'

    def get_queryset(self):
        return super().get_queryset().filter(
            learning_unit_year__academic_year__year=self.kwargs['year'],
            learning_unit_year__acronym__icontains=self.kwargs['acronym'],
        )
