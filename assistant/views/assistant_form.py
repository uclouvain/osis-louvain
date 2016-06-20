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
from django.contrib.auth.decorators import login_required
from assistant.models import mandate_structure, academic_assistant, assistant_mandate
from django.db.models import Q
from base.models import person, person_address, academic_year, learning_unit_year, offer_year, program_manager
from django.template.context_processors import request
from assistant.forms import AssistantFormPart1
    
@login_required
def assistant_pst_part1(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    assistant = mandate.assistant
    addresses_pst = person_address.find_by_person(assistant.person)
    form = AssistantFormPart1(initial={'inscription': assistant.inscription,
                                       'phd_inscription_date': assistant.phd_inscription_date,
                                       'confirmation_test_date': assistant.confirmation_test_date,
                                       'thesis_date': assistant.thesis_date,
                                       'supervisor': assistant.supervisor,
                                       'external_functions': mandate.external_functions,
                                       'external_contract': mandate.external_contract,
                                       'justification': mandate.justification})
    return render(request, "assistant_form_part1.html", {'assistant': assistant,
                                                         'addresses': addresses_pst,
                                                         'mandate': mandate,
                                                         'form': form}) 
    
@login_required    
def pst_form_part1_save(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    addresses_pst = person_address.find_by_person(mandate.assistant.person)
    form = AssistantFormPart1(data=request.POST, instance=mandate.assistant)
    if form.is_valid():
        form.save()
        return True
    else:
        return render(request, "assistant_form_part1.html", {'assistant': mandate.assistant,
                                                         'addresses': addresses_pst,
                                                         'mandate': mandate,
                                                         'form': form}) 
