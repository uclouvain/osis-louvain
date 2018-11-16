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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import functools
import operator

from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchVector, TrigramSimilarity
from django.db.models import Q, Value
from django.db.models.functions import Concat

from base.models.person import Person


class EmployeeAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.employees.all()
        if self.q:
            qs = qs.filter(
                Q(last_name__icontains=self.q) |
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(global_id=self.q)
            )
        return qs.order_by("last_name", "first_name")

    def get_result_label(self, result):
        return "{last_name} {first_name}".format(last_name=result.last_name, first_name=result.first_name)
