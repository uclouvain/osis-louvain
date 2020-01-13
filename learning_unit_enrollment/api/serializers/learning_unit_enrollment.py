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

from rest_framework import serializers

from base.models.learning_unit_enrollment import LearningUnitEnrollment
from education_group.api.serializers.education_group import EducationGroupYearHyperlinkedIdentityField
from learning_unit_enrollment.api.serializers.utils import LearningUnitHyperlinkedIdentityField


class LearningUnitEnrollmentSerializer(serializers.ModelSerializer):

    registration_id = serializers.CharField(
        source='offer_enrollment.student.registration_id',
        read_only=True,
    )
    student_first_name = serializers.CharField(
        source='offer_enrollment.student.person.first_name',
        read_only=True,
    )
    student_last_name = serializers.CharField(
        source='offer_enrollment.student.person.last_name',
        read_only=True,
    )
    student_email = serializers.CharField(
        source='offer_enrollment.student.person.email',
        read_only=True,
    )
    learning_unit_acronym = serializers.CharField(
        source='learning_unit_year.acronym',
        read_only=True,
    )
    education_group_acronym = serializers.CharField(
        source='offer_enrollment.education_group_year.acronym',
        read_only=True,
    )
    academic_year = serializers.IntegerField(
        source='learning_unit_year.academic_year.year',
        read_only=True,
    )
    education_group_url = EducationGroupYearHyperlinkedIdentityField(
        read_only=True,
        lookup_field='offer_enrollment__education_group_year',
    )
    learning_unit_url = LearningUnitHyperlinkedIdentityField(read_only=True)

    learning_unit_enrollment_state = serializers.CharField(
        read_only=True,
        source='enrollment_state',
    )
    offer_enrollment_state = serializers.CharField(
        read_only=True,
        source='offer_enrollment.enrollment_state',
    )

    class Meta:
        model = LearningUnitEnrollment
        fields = (
            'registration_id',
            'student_first_name',
            'student_last_name',
            'student_email',
            'learning_unit_acronym',
            'education_group_acronym',
            'academic_year',
            'education_group_url',
            'learning_unit_url',
            'learning_unit_enrollment_state',
            'offer_enrollment_state',
        )
