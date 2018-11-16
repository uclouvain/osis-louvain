############################################################################
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
from django.utils.translation import ugettext as _

from base.business.education_groups.postponement import ConsistencyError
from base.models.academic_year import AcademicYear, compute_max_academic_year_adjournment


class AutomaticPostponement(ABC):
    """
    Abstract class:
        This class manages the postponement of annualized objects from N+5 to N+6
    """
    # The model must have an FK to academic_year
    model = None

    # Callbacks
    # They should be call with __func__ to be staticmethod
    send_before = None
    send_after = None
    extend_method = None

    msg_result = _("%(number_extended)s object(s) extended and %(number_error)s error(s)")

    def __init__(self, queryset=None):

        # Fetch N+6 and N+5 academic_years
        self.last_academic_year = AcademicYear.objects.get(year=compute_max_academic_year_adjournment())
        self.penultimate_academic_year = self.last_academic_year.past()

        self.queryset = self.get_queryset(queryset)
        self.already_duplicated = self.get_already_duplicated()
        self.to_not_duplicate = self.get_to_not_duplicated()
        self.to_duplicate = self.queryset.difference(self.already_duplicated, self.to_not_duplicate)

        self.result = []
        self.errors = []

    def postpone(self):
        # send statistics to the managers
        self.send_before.__func__(self.last_academic_year, self.to_duplicate,
                                  self.already_duplicated, self.to_not_duplicate)

        self._extend_objects()

        # send statistics with results to the managers
        self.send_after.__func__(self.last_academic_year, self.result, self.already_duplicated,
                                 self.to_not_duplicate, self.errors)

        return self.result, self.errors

    def _extend_objects(self):
        for obj in self.to_duplicate:
            try:
                with transaction.atomic():
                    self.result.append(self.extend_obj(obj, self.last_academic_year))

            # General catch to be sure to not stop the rest of the duplication
            except (Error, ObjectDoesNotExist, MultipleObjectsReturned, ConsistencyError):
                self.errors.append(obj)

    @classmethod
    def extend_obj(cls, obj, last_academic_year):
        return cls.extend_method(obj, last_academic_year)

    def get_queryset(self, queryset=None):
        """ Override if you need to add additional filters"""
        if not queryset:
            queryset = self.model.objects.all()
        return queryset.filter(academic_year=self.penultimate_academic_year)

    def get_already_duplicated(self):
        """ Should return queryset of already existing objects """
        raise NotImplementedError

    def get_to_not_duplicated(self):
        """ Should return queryset of objects to not duplicate """
        raise NotImplementedError

    def serialize_postponement_results(self):
        return {
            "msg": self.msg_result % {'number_extended': len(self.result), 'number_error': len(self.errors)},
            "errors": [str(obj) for obj in self.errors]
        }
