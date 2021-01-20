#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import List

from django.db.models import Model

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_year import EducationGroupYear
from base.models.enums.admission_condition_sections import ConditionSectionsTypes
from base.tests.factories.admission_condition import AdmissionConditionLineFactory, AdmissionConditionFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class TestAdmissionConditionMixin:
    SECTION = "ca_maitrise_fr"
    LINE_SECTION = ConditionSectionsTypes.ucl_bachelors.name

    def generate_condition_data(self):
        self.admission_condition = AdmissionConditionFactory(education_group_year__academic_year__current=True)
        self.education_group_year = self.admission_condition.education_group_year
        self.next_year_education_group_year = EducationGroupYearFactory.next_year_from(self.education_group_year)

    def generate_condition_line_data(self):
        self.admission_condition_line = AdmissionConditionLineFactory(
            admission_condition__education_group_year__academic_year__current=True,
            section=self.LINE_SECTION
        )
        self.other_admission_condition_line = AdmissionConditionLineFactory(
            admission_condition=self.admission_condition_line.admission_condition,
            section=self.LINE_SECTION
        )
        self.admission_condition = self.admission_condition_line.admission_condition
        self.education_group_year = self.admission_condition.education_group_year
        self.next_year_education_group_year = EducationGroupYearFactory.next_year_from(self.education_group_year)

    def assert_conditions_equal(self, obj: 'EducationGroupYear', other_obj: 'EducationGroupYear', fields: List[str]):
        base_conditions = AdmissionCondition.objects.get(education_group_year=obj)
        to_compare_conditions = AdmissionCondition.objects.get(education_group_year=other_obj)

        self._assert_model_equal(base_conditions, to_compare_conditions, fields_to_compare=fields)

    def assert_conditions_line_equal(self, obj: 'EducationGroupYear', other_obj: 'EducationGroupYear', section: str):
        base_conditions_line = AdmissionConditionLine.objects.filter(
            admission_condition__education_group_year=obj,
            section=section
        )

        to_compare_conditions_line = AdmissionConditionLine.objects.filter(
            admission_condition__education_group_year=other_obj,
            section=section
        )

        for condition_line, other_condition_line in zip(base_conditions_line, to_compare_conditions_line):
            self._assert_model_equal(condition_line, other_condition_line)

    def _assert_model_equal(self, obj: 'Model', other_obj: 'Model', fields_to_compare=None):
        if not fields_to_compare:
            fields_not_compare = (
                "external_id",
                "changed",
                "uuid",
                "id",
                "education_group_year_id",
                "admission_condition_id"
            )
            model_fields = obj._meta.fields
            fields_to_compare = [field.attname for field in model_fields if field.attname not in fields_not_compare]
        for field in fields_to_compare:
            self.assertEqual(getattr(obj, field), getattr(other_obj, field), field)

