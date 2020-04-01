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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.test import TestCase

from base.models.education_group_year import EducationGroupYear
from base.models.enums import duration_unit
from base.scripts.generate_11_ba_from_1_ba import generate_11_ba_from_1_ba
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class Generate11BAFrom1BATest(TestCase):
    def setUp(self):
        self.existing_acronym = "ABCD1BA"
        self.number_of_education_group_years_to_create = 6
        self.title_fr = "Bachelier en Droit"
        self.title_en = "Bachelor in Law"
        self.academic_years = AcademicYearFactory.produce_in_future(
            quantity=self.number_of_education_group_years_to_create
        )

        education_group = EducationGroupFactory()
        [
            EducationGroupYearFactory(
                academic_year=anac,
                acronym=self.existing_acronym,
                education_group=education_group,
                title=self.title_fr,
                title_english=self.title_en
            )
            for anac in self.academic_years
        ]

    def test_generate_11_ba_from_1_ba(self):
        generate_11_ba_from_1_ba(self.existing_acronym)
        new_acronym = "ABCD11BA"
        created_education_group_years = EducationGroupYear.objects.filter(acronym=new_acronym)

        self.assertEqual(
            self.number_of_education_group_years_to_create,
            created_education_group_years.count()
        )

        first_created_education_group_year = created_education_group_years.first()
        self.assertEqual(
            first_created_education_group_year.duration,
            2
        )
        self.assertEqual(
            first_created_education_group_year.duration_unit,
            duration_unit.DurationUnits.QUADRIMESTER.value
        )
        self.assertEqual(
            first_created_education_group_year.title,
            "Première année de bachelier en Droit"
        )
        self.assertEqual(
            first_created_education_group_year.title_english,
            "First year of the Bachelor in Law"
        )
        self.assertEqual(
            first_created_education_group_year.acronym,
            new_acronym
        )
        self.assertEqual(
            first_created_education_group_year.acronym,
            new_acronym
        )
        self.assertEqual(
            first_created_education_group_year.diploma_printing_title,
            ''
        )

        self.assertIsNone(first_created_education_group_year.external_id)
        self.assertIsNone(first_created_education_group_year.partial_acronym)
        self.assertIsNone(first_created_education_group_year.credits)
        self.assertIsNone(first_created_education_group_year.internship)
        self.assertFalse(first_created_education_group_year.joint_diploma)
