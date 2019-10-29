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
from django.utils import timezone
from django.utils.functional import cached_property

from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin

LEARNING_UNIT_CREATION_SPAN_YEARS = 6
MAX_ACADEMIC_YEAR_FACULTY = 2
MAX_ACADEMIC_YEAR_CENTRAL = 6


class AcademicYearAdmin(SerializableModelAdmin):
    list_display = ('name', 'start_date', 'end_date')


class AcademicYearQuerySet(models.QuerySet):
    def min_max_years(self, min_year, max_year):
        return self.filter(year__gte=min_year, year__lte=max_year)

    def currents(self, date=None):
        if not date:
            date = timezone.now()

        return self.filter(start_date__lte=date, end_date__gte=date)

    def current(self, date=None):
        """ If we have two academic year [2015-2016] [2016-2017]. It will return [2016-2017] """
        return self.currents(date).last()

    def max_adjournment(self, delta=0):
        date = timezone.now()
        max_date = date.replace(year=date.year + LEARNING_UNIT_CREATION_SPAN_YEARS + delta)
        return self.current(max_date)


class AcademicYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    year = models.IntegerField(unique=True)
    start_date = models.DateField(default=timezone.now, blank=True, null=True)
    end_date = models.DateField(default=timezone.now, blank=True, null=True)

    objects = AcademicYearQuerySet.as_manager()

    @property
    def name(self):
        return self.__str__()

    @property
    def is_even(self):
        return self.year % 2 == 0

    @property
    def is_odd(self):
        return self.year % 2 == 1

    def save(self, *args, **kwargs):
        if self.start_date and self.year != self.start_date.year:
            raise AttributeError("The start date should be in the same year of the academic year.")
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise AttributeError("Start date should be before the end date.")
        if find_academic_years(self.start_date, self.end_date).count() >= 2:
            raise AttributeError("We cannot have more than two academic year in date range")
        super(AcademicYear, self).save(*args, **kwargs)

    def __str__(self):
        return u"%s-%s" % (self.year, str(self.year + 1)[-2:])

    class Meta:
        ordering = ["year"]
        permissions = (
            ("can_access_academicyear", "Can access academic year"),
        )

    @cached_property
    def is_past(self):
        return self.year < starting_academic_year().year

    def next(self):
        return AcademicYear.objects.get(year=self.year + 1)

    def past(self):
        return AcademicYear.objects.get(year=self.year - 1)


def find_academic_year_by_id(academic_year_id):
    return AcademicYear.objects.get(pk=academic_year_id)


def find_academic_year_by_year(year):
    try:
        return AcademicYear.objects.get(year=year)
    except AcademicYear.DoesNotExist:
        return None


def find_academic_years(start_date=None, end_date=None, start_year=None, end_year=None):
    """"Return all academic years ordered by year

        Keyword arguments:
            start_date -- (default None)
            end_date -- (default None)
            start_year -- (default None)
            end_year -- (default None)
    """
    queryset = AcademicYear.objects.all()
    if start_date is not None:
        queryset = queryset.filter(start_date__lte=start_date)
    if end_date is not None:
        queryset = queryset.filter(end_date__gte=end_date)
    if start_year is not None:
        queryset = queryset.filter(year__gte=start_year)
    if end_year is not None:
        queryset = queryset.filter(year__lte=end_year)

    return queryset.order_by('year')


def current_academic_years():
    return AcademicYear.objects.currents()


def current_academic_year():
    """ If we have two academic year [2015-2016] [2016-2017]. It will return [2015-2016] """
    return current_academic_years().first()


def starting_academic_year():
    """ If we have two academic year [2015-2016] [2016-2017]. It will return [2016-2017] """
    return current_academic_years().last()


def compute_max_academic_year_adjournment():
    return starting_academic_year().year + LEARNING_UNIT_CREATION_SPAN_YEARS
