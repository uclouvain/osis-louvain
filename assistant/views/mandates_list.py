##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import render
from assistant.models import assistant_mandate
from base.models import academic_year
from django.views.generic import ListView


class MandatesListView(ListView):
    context_object_name = 'mandates_list'
    template_name = 'mandates_list.html'
    
    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        return context
    
    def get_queryset(self):
        this_academic_year = academic_year.current_academic_year()
        return assistant_mandate.AssistantMandate.objects.filter(academic_year=this_academic_year)



