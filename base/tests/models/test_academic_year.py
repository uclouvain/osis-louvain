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
import datetime

from django.test import TestCase
from django.utils import timezone

from base.models import academic_year
from base.models.academic_year import AcademicYear
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year

now = datetime.datetime.now()


def create_academic_year(year=now.year):
    return AcademicYearFactory(year=year)


class MultipleAcademicYearTest(TestCase):
    def setUp(self):
        AcademicYearFactory(year=(now.year - 1),
                            start_date=datetime.datetime(now.year - 1, now.month, 15),
                            end_date=datetime.datetime(now.year, now.month, 28))
        AcademicYearFactory(year=now.year,
                            start_date=datetime.datetime(now.year, now.month, 1),
                            end_date=datetime.datetime(now.year + 1, now.month, 28))

    def test_find_academic_years(self):
        today = datetime.date.today()
        academic_yrs = academic_year.find_academic_years(start_date=today, end_date=today)
        current_academic_yr = academic_year.current_academic_year()
        starting_academic_yr = academic_year.starting_academic_year()
        nb_of_academic_yrs = academic_yrs.count()
        if starting_academic_yr != current_academic_yr:
            self.assertEqual(nb_of_academic_yrs, 2)
        else:
            self.assertEqual(nb_of_academic_yrs, 1)

    def test_current_academic_year(self):
        current_academic_yr = academic_year.current_academic_year()
        starting_academic_yr = academic_year.starting_academic_year()
        if starting_academic_yr != current_academic_yr:
            self.assertEqual(current_academic_yr.year, now.year - 1)
        else:
            self.assertEqual(current_academic_yr.year, now.year)

    def test_starting_academic_year(self):
        academic_yr = academic_year.starting_academic_year()
        self.assertEqual(academic_yr.year, now.year)


class SingleAcademicYearTest(TestCase):
    def test_starting_equalto_current(self):
        start_date = timezone.now() - datetime.timedelta(days=5)
        end_date = start_date + datetime.timedelta(days=220)
        academic_yr = AcademicYearFactory(year=start_date.year, start_date=start_date, end_date=end_date)
        starting_academic_year = academic_year.starting_academic_year()
        self.assertEqual(starting_academic_year.year, academic_yr.year)


class PeriodAcademicYearTest(TestCase):
    def test_start_date_year_same_of_year(self):
        academic_year = AcademicYearFactory.build(year=now.year,
                                                  start_date=datetime.datetime(now.year + 1, now.month, 15),
                                                  end_date=datetime.datetime(now.year + 1, now.month, 28))
        with self.assertRaises(AttributeError):
            academic_year.save()

    def test_start_date_before_end_date(self):
        academic_year = AcademicYearFactory.build(year=now.year,
                                                  start_date=datetime.datetime(now.year, now.month, 15),
                                                  end_date=datetime.datetime(now.year, now.month, 15))
        with self.assertRaises(AttributeError):
            academic_year.save()

    def test_more_than_two_academic_year_in_same_period(self):
        academic_year.AcademicYear.objects.create(year=2015,
                                                  start_date=datetime.datetime(2015, 9, 15),
                                                  end_date=datetime.datetime(2017, 12, 30))
        academic_year.AcademicYear.objects.create(year=2016,
                                                  start_date=datetime.datetime(2016, 9, 15),
                                                  end_date=datetime.datetime(2017, 12, 30))
        with self.assertRaises(AttributeError):
            academic_year.AcademicYear.objects.create(year=2017,
                                                      start_date=datetime.datetime(2017, 9, 14),
                                                      end_date=datetime.datetime(2017, 9, 30))


class AcademicYearNextPropertyTest(TestCase):
    def setUp(self):
        self.current_ac = create_current_academic_year()
        self.next_ac = AcademicYearFactory(year=self.current_ac.year + 1)

    def test_next_property_case_have_next(self):
        self.assertEqual(self.current_ac.next(), self.next_ac)

    def test_next_property_case_doesnt_have_next(self):
        with self.assertRaises(AcademicYear.DoesNotExist):
            self.next_ac.next()


class AcademicYearPastPropertyTest(TestCase):
    def setUp(self):
        self.current_ac = create_current_academic_year()
        self.prev_ac = AcademicYearFactory(year=self.current_ac.year - 1)

    def test_next_property_case_have_next(self):
        self.assertEqual(self.current_ac.past(), self.prev_ac)

    def test_next_property_case_doesnt_have_next(self):
        with self.assertRaises(AcademicYear.DoesNotExist):
            self.prev_ac.past()