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
from abc import ABC, abstractmethod

from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from base.models.academic_calendar import get_academic_calendar_by_date_and_reference_and_data_year, AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums import academic_calendar_type


class EventPerm(ABC):
    @classmethod
    @abstractmethod
    def is_open(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def __is_open_for_spec_egy(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def __is_open_other_rules(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_academic_years(*args, **kwargs) -> QuerySet:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_academic_years_ids(cls, *args, **kwargs) -> QuerySet:
        raise NotImplementedError


class EventPermEducationGroupEdition(EventPerm):
    @classmethod
    def is_open(cls, *args, **kwargs):
        if kwargs.get('education_group'):
            return cls.__is_open_for_spec_egy(*args, **kwargs)
        return cls.__is_open_other_rules(*args, **kwargs)

    @classmethod
    def __is_open_for_spec_egy(cls, *args, **kwargs):
        aca_year = kwargs.get('education_group').academic_year
        academic_calendar = get_academic_calendar_by_date_and_reference_and_data_year(
            aca_year, academic_calendar_type.EDUCATION_GROUP_EDITION)
        if kwargs.get('in_range'):
            return academic_calendar
        error_msg = None
        if not academic_calendar:
            error_msg = _("This education group is not editable during this period.")

        result = error_msg is None
        if kwargs.get('raise_exception', False) and not result:
            raise PermissionDenied(_(error_msg).capitalize())
        return result

    @classmethod
    def __is_open_other_rules(cls, *args, **kwargs):
        return cls.__is_calendar_opened(*args, **kwargs)

    @staticmethod
    def __is_calendar_opened(*args, **kwargs):
        return AcademicCalendar.objects.open_calendars()\
            .filter(reference=academic_calendar_type.EDUCATION_GROUP_EDITION)\
            .exists()

    @classmethod
    def get_academic_years(cls, *args, **kwargs) -> QuerySet:
        return AcademicYear.objects.filter(pk__in=cls.get_academic_years_ids())

    @classmethod
    def get_academic_years_ids(cls, *args, **kwargs) -> QuerySet:
        return AcademicCalendar.objects.open_calendars()\
            .filter(reference=academic_calendar_type.EDUCATION_GROUP_EDITION)\
            .values_list('data_year', flat=True)
