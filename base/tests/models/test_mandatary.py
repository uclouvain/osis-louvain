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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from django.test import TestCase
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.mandate import MandateFactory
from base.tests.factories.mandatary import MandataryFactory
from base.models.enums import mandate_type as mandate_types
from base.models import mandatary


class MandataryTest(TestCase):
    def setUp(self):
        today = datetime.date.today()
        # academic year 1
        self.start_date_ay_1 = today.replace(year=today.year - 3)
        self.end_date_ay_1 = today.replace(year=today.year - 2)
        academic_year_1 = AcademicYearFactory.build(start_date=self.start_date_ay_1,
                                                    end_date=self.end_date_ay_1,
                                                    year=today.year - 3)
        academic_year_1.save()
        # academic year 1
        self.start_date_ay_2 = today.replace(year=today.year - 2)
        self.end_date_ay_2 = today.replace(year=today.year - 1)
        academic_year_2 = AcademicYearFactory.build(start_date=self.start_date_ay_2,
                                                    end_date=self.end_date_ay_2,
                                                    year=today.year - 2)
        academic_year_2.save()
        self.an_education_group = EducationGroupFactory()
        # education group year for acy 1
        self.education_group_year_acy1_1 = EducationGroupYearFactory(education_group=self.an_education_group,
                                                                academic_year=academic_year_1)
        education_group_year_acy1_2 = EducationGroupYearFactory(education_group=self.an_education_group,
                                                                academic_year=academic_year_1)
        # education group year for acy 2
        education_group_year_acy2_1 = EducationGroupYearFactory(education_group=self.an_education_group,
                                                                academic_year=academic_year_2)
        # mandates
        self.mandate_secretary = MandateFactory(education_group=self.an_education_group, function=mandate_types.SECRETARY)
        self.mandate_president = MandateFactory(education_group=self.an_education_group, function=mandate_types.PRESIDENT)
        # Mandataries during academic year 1 period
        self.mandatary_secretary_egy1 = MandataryFactory(mandate=self.mandate_secretary,
                                                    start_date=self.start_date_ay_1,
                                                    end_date=self.end_date_ay_1)
        self.mandatary_president_egy1 = MandataryFactory(mandate=self.mandate_president,
                                                    start_date=self.start_date_ay_1,
                                                    end_date=self.end_date_ay_1)

        # Mandataries during academic year 2 period
        mandatary_secretary_egy_2 = MandataryFactory(mandate=self.mandate_secretary,
                                                     start_date=self.start_date_ay_2,
                                                     end_date=self.end_date_ay_2)
    def test_find_by_education_group_year(self):




        self.assertListEqual(list(mandatary.find_by_education_group_year(self.education_group_year_acy1_1)),
                             [self.mandatary_president_egy1, self.mandatary_secretary_egy1])

    def test_find_by_education_group_year_function(self):
        self.assertListEqual(list(mandatary.find_by_education_group_year_function(self.education_group_year_acy1_1, mandate_types.SECRETARY )),
                             [self.mandatary_secretary_egy1])