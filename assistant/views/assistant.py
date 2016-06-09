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
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from base.models import person, academic_year
from assistant.models import academic_assistant, assistant_mandate
from django.http.response import HttpResponseRedirect
from django.views.generic.list import ListView

@login_required
def assistant_check(request):
    try: 
        academic_assistant.find_by_person(person.find_by_user(request.user))
        return HttpResponseRedirect(reverse('assistant_mandates'))
    except:
        return HttpResponseRedirect(reverse('assistants_home'))

class AssistantMandatesListView(ListView): 
    context_object_name = 'assistant_mandates_list'
    template_name = 'assistant_mandates.html'

    def get_queryset(self):
        assistant = academic_assistant.find_by_person(person.find_by_user(self.request.user))
        this_academic_year = academic_year.current_academic_year()
        return assistant_mandate.find_mandate_by_assistant_for_academic_year(assistant, this_academic_year)
        
    def get_context_data(self, **kwargs):
        context = super(AssistantMandatesListView, self).get_context_data(**kwargs)
        context['assistant'] = academic_assistant.find_by_person(person.find_by_user(self.request.user))
        return context
        
       
    
