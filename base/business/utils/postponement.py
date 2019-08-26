############################################################################
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
############################################################################
from abc import ABC

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction, Error
from django.db.models import Max, Q, F
from django.utils.translation import gettext as _

from base.business.education_groups.postponement import ConsistencyError
from base.models.academic_year import AcademicYear


class AutomaticPostponement(ABC):
    # The model must have annualized data with a FK to AcademicYear
    model = None

    msg_result = _("%(number_extended)s object(s) extended and %(number_error)s error(s)")

    def __init__(self, queryset=None):
        self.current_year = AcademicYear.objects.current()

        self.queryset = self.get_queryset(queryset)

        self.already_duplicated = self.get_already_duplicated()
        self.to_not_duplicate = self.get_to_not_duplicated()
        self.ending_on_max_adjournment = self.get_ending_on_max_adjournment()

        if self.already_duplicated or self.to_not_duplicate:
            self.to_duplicate = self.queryset.difference(self.already_duplicated, self.to_not_duplicate)
        else:
            self.to_duplicate = self.queryset

        self.result = []  # Contains the list of postponed objects.
        self.errors = []

    def postpone(self):
        raise NotImplementedError

    def get_queryset(self, queryset=None):
        """ Override if you need to add additional filters"""
        if not queryset:
            queryset = self.model.objects.all()
        return queryset

    def get_already_duplicated(self):
        return self.model.objects.none()

    def get_to_not_duplicated(self):
        return self.model.objects.none()

    def get_ending_on_max_adjournment(self):
        return self.model.objects.none()

    def serialize_postponement_results(self):
        return {
            "msg": self.msg_result % {'number_extended': len(self.result), 'number_error': len(self.errors)},
            "errors": [str(obj) for obj in self.errors]
        }

    def post_extend(self, original_object, list_postponed_objects):
        """ Allow the user to add actions to execute after the postponement of an object """
        pass


class AutomaticPostponementToN6(AutomaticPostponement):
    """
    Abstract class:
        This class manages the postponement of annualized objects from N to N+6
        It will detected the end year of the instance and adapt its postponement.
    """

    # The model must have annualized data with a FK to AcademicYear
    annualized_set = ""

    # Callbacks
    # They should be call with __func__ to be staticmethod
    extend_method = None
    send_before = None
    send_after = None

    def __init__(self, queryset=None):
        # Fetch the N and N+6 academic_years
        self.last_academic_year = AcademicYear.objects.max_adjournment()
        self.current_year = AcademicYear.objects.current()

        super().__init__(queryset)

        self.queryset = self.get_queryset(queryset)

    def postpone(self):
        # send statistics to the managers
        statistics_context = self.get_statistics_context()
        self.send_before.__func__(statistics_context)

        self._extend_objects()

        # send statistics with results to the managers
        self.send_after.__func__(statistics_context, self.result, self.errors)

        return self.result, self.errors

    def _extend_objects(self):
        for obj in self.to_duplicate:
            try:
                with transaction.atomic():
                    last_year = obj.end_year or self.last_academic_year.year
                    obj_to_copy = getattr(obj, self.annualized_set + "_set").latest('academic_year__year')
                    copied_objs = []
                    for year in range(obj.last_year + 1, last_year + 1):
                        new_obj = self.extend_obj(obj_to_copy, AcademicYear.objects.get(year=year))
                        copied_objs.append(new_obj)

                    self.post_extend(obj_to_copy, copied_objs)
                    self.result.extend(copied_objs)

            # General catch to be sure to not stop the rest of the duplication
            except (Error, ObjectDoesNotExist, MultipleObjectsReturned, ConsistencyError):
                self.errors.append(obj)

    @classmethod
    def extend_obj(cls, obj, last_academic_year):
        return cls.extend_method(obj, last_academic_year)

    def get_queryset(self, queryset=None):
        """ Override if you need to add additional filters"""
        queryset = super().get_queryset(queryset)

        # Annotate the latest year with an annualized data.
        return queryset.annotate(
            last_year=Max(self.annualized_set + '__academic_year__year')
        )

    def get_already_duplicated(self):
        return self.queryset.filter(last_year__gte=self.last_academic_year.year)

    def get_to_not_duplicated(self):
        """ We cannot postpone an education_group in the past """
        return self.queryset.filter(
            Q(last_year__lt=self.current_year.year) | Q(end_year__lt=self.last_academic_year.year)
        )

    def get_ending_on_max_adjournment(self):
        return self.queryset.filter(end_year=self.last_academic_year.year)

    def get_statistics_context(self):
        """ Override if you need to add additional values to statistics"""
        return {
            'max_academic_year_to_postpone': self.last_academic_year,
            'to_duplicate': self.to_duplicate,
            'already_duplicated':  self.already_duplicated,
            'to_ignore': self.to_not_duplicate,
            'ending_on_max_academic_year': self.ending_on_max_adjournment,
        }
