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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import ListView

from base.models.person import Person
from base.models.student import Student


class UserListView(LoginRequiredMixin, ListView):
    model = Person
    paginate_by = "20"
    ordering = 'last_name', 'first_name', 'global_id'
    # template_name = ''

    def get_queryset(self):
        qs = super().get_queryset().select_related('user')\
                    .prefetch_related('managed_entities',
                                      'personentity_set',
                                      'partnershipentitymanager_set',
                                      'programmanager_set',
                                      'user__groups')\
                    .filter(user__is_active=True)\
                    .exclude(user__groups__name='tutors')\
                    .exclude(pk__in=Student.objects.all().values_list('person_id', flat=True))
        return qs

    def paginate_queryset(self, queryset, page_size):
        """ The cache can store a wrong page number,
        In that case, we return to the first page.
        """
        try:
            return super().paginate_queryset(queryset, page_size)
        except Http404:
            self.kwargs['page'] = 1

        return super().paginate_queryset(queryset, page_size)
