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
import os
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http.response import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from assistant.models import *
from base.models import person, person_address, academic_year, learning_unit_year, offer_year, program_manager
from django.template.context_processors import request
from assistant.forms import AssistantFormPart1, AssistantFormPart3
from assistant.models.academic_assistant import find_by_id
from assistant.models.assistant_mandate import find_mandate_by_id,\
    find_mandate_by_academic_assistant
from base.models.person import find_by_user
from assistant.forms import AssistantDocumentForm, FilesInLineFormSet


def user_is_assistant(user):
    """Use with a ``user_passes_test`` decorator to restrict access to 
    authenticated users who are assistant for the mandate_id."""
    
    try:
        if user.is_authenticated():
            return academic_assistant.AcademicAssistant.objects.get(person=user.person)
    except ObjectDoesNotExist:
        return False
    
@login_required
def assistant_pst_part1(request):
    academic_assistant = find_by_id (person.find_by_user(request.user).id)
    addresses_pst = person_address.find_by_person(academic_assistant.person)
    assistant_birthday = find_by_user(request.user).birth_date
    assistant_courses = program_manager.find_by_person(person.Person(academic_assistant.id))
    mandate = find_mandate_by_academic_assistant(academic_assistant)
    assistant_faculty = mandate_structure.MandateStructure.objects.filter(assistant_mandate=mandate)
    form = AssistantFormPart1(initial={'inscription': academic_assistant.inscription,
                                       'phd_inscription_date': academic_assistant.phd_inscription_date,
                                       'confirmation_test_date': academic_assistant.confirmation_test_date,
                                       'thesis_date': academic_assistant.thesis_date,
                                       'supervisor': academic_assistant.supervisor,
                                       'external_functions': mandate.external_functions,
                                       'external_contract': mandate.external_contract,
                                       'justification': mandate.justification})
    return render(request, "assistant_form_part1.html", {'assistant': academic_assistant,
                                                         'birthday': assistant_birthday,
                                                         'addresses': addresses_pst,
                                                         'courses': assistant_courses,
                                                         'mandate': mandate,
                                                         'faculty': assistant_faculty,
                                                         'form': form}) 
    
@login_required    
def pst_form_part1_save(request, mandate_id):
    form = AssistantFormPart1(data=request.POST)
    assistant_mandate = find_mandate_by_id(mandate_id)
    academic_assistant = find_mandate_by_academic_assistant(assistant_mandate.assistant)
    
    # get the screen modifications   
    if request.POST['inscription']:
        academic_assistant.inscription = request.POST['inscription']
    else:
        academic_assistant.inscription = None
        
    if request.POST['expected_phd_date']:
        academic_assistant.expected_phd_date = request.POST['expected_phd_date']
    else:
        academic_assistant.expected_phd_date = None    
        
    if request.POST['phd_inscription_date']:
        academic_assistant.phd_inscription_date = request.POST['phd_inscription_date']
    else:
        academic_assistant.phd_inscription_date = None

    if request.POST['supervisor']:
        academic_assistant.supervisor = request.POST['supervisor']
    else:
        academic_assistant.supervisor = None

    if request.POST['confirmation_test_date']:
        academic_assistant.confirmation_test_date = request.POST['confirmation_test_date']
    else:
        academic_assistant.confirmation_test_date = None

    if request.POST['thesis_date']:
        academic_assistant.thesis_date = request.POST['thesis_date']
    else:
        academic_assistant.thesis_date = None

    if request.POST['external_functions']:
        assistant_mandate.external_functions = request.POST['external_functions']
    else:
        assistant_mandate.external_functions = None

    if request.POST['external_contract']:
        assistant_mandate.external_contract = request.POST['external_contract']
    else:
        assistant_mandate.external_contract = None

    if request.POST['justification']:
        assistant_mandate.justification = request.POST['justification']
    else:
        assistant_mandate.justification = None

    if form.is_valid():
        academic_assistant.save()
        assistant_mandate.save()
        return assistant_pst_part1(request, academic_assistant.id)
    else:
        form = AssistantFormPart1()
        return render(request, "assistant_form_part2.html")  
    
    
@user_passes_test(user_is_assistant, login_url='assistants_home') 
def form_part3_edit(request, mandate_id):
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    person = request.user.person
    assistant = mandate.assistant
    if person != assistant.person:
        return HttpResponseRedirect(reverse('assistant_mandates'))
    form = AssistantFormPart3(initial={'phd_inscription_date': assistant.phd_inscription_date,
                                       'confirmation_test_date': assistant.confirmation_test_date,
                                       'thesis_title': assistant.thesis_title,
                                       'confirmation_test_date': assistant.confirmation_test_date,
                                       'remark': assistant.remark,
                                       }, prefix='mand')
    
    formset = FilesInLineFormSet(instance=mandate,queryset =
assistant_document.AssistantDocument.objects.filter(doc_type='PHD'), prefix='files',
initial=[{'assistant': assistant, 'doc_type': 'PHD'}])
    
    return render(request, "assistant_form_part3.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'form': form,
                                                         'formset': formset}) 

@user_passes_test(user_is_assistant, login_url='assistants_home')    
def form_part3_save(request, mandate_id):
    """Use to save an assistant form part3."""
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    assistant = mandate.assistant
    person = request.user.person
    if person != assistant.person:
        return HttpResponseRedirect(reverse('assistant_mandates'))
    elif request.method == 'POST':
        if 'add_file' in request.POST:
            form = AssistantDocumentForm(initial={'mandate': mandate,
                                       'assistant': assistant,
                                       'doc_type': 'PHD'
                                       }, prefix='file')
            return render(request, "add_file.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'form': form}) 
        else:
            form = AssistantFormPart3(data=request.POST, instance=assistant, prefix='mand')
            formset = FilesInLineFormSet(request.POST, request.FILES, instance=mandate, prefix='files')
            if form.is_valid() and formset.is_valid():
                form.save()
                formset.save()
                return form_part3_edit(request, mandate.id)
            else:
                return render(request, "assistant_form_part3.html", {'assistant': assistant,
                                                             'mandate': mandate,
                                                             'form': form,
                                                             'formset': formset}) 
        