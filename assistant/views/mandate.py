##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.decorators import user_passes_test
from assistant.forms import MandateForm, structure_inline_formset
from assistant import models as assistant_mdl
from base.views import layout
from django.core.exceptions import ObjectDoesNotExist


def user_is_manager(user):
    """Use with a ``user_passes_test`` decorator to restrict access to 
    authenticated users who are manager."""
    
    try:
        if user.is_authenticated():
            return assistant_mdl.manager.Manager.objects.get(person=user.person)
    except ObjectDoesNotExist:
        return False
    

@user_passes_test(user_is_manager, login_url='assistants_home')
def mandate_edit(request, mandate_id):
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    form = MandateForm(initial={'comment': mandate.comment,
                                'renewal_type': mandate.renewal_type,
                                'absences': mandate.absences,
                                'other_status': mandate.other_status,
                                'contract_duration': mandate.contract_duration,
                                'contract_duration_fte': mandate.contract_duration_fte
                                }, prefix="mand", instance=mandate)
    formset = structure_inline_formset(instance=mandate, prefix="struct")
    
    return layout.render(request, 'mandate_form.html', {'mandate': mandate, 'form': form, 'formset': formset})


@user_passes_test(user_is_manager, login_url='assistants_home')
def mandate_save(request, mandate_id):
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    form = MandateForm(data=request.POST, instance=mandate, prefix='mand')
    formset = structure_inline_formset(request.POST, request.FILES, instance=mandate, prefix='struct')
    if form.is_valid():
        form.save()
        if formset.is_valid():
            formset.save()
            return mandate_edit(request, mandate.id)
        else:
            return layout.render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset})
    else:
        return layout.render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset})


@user_passes_test(user_is_manager, login_url='assistants_home')
def load_mandates(request):
    return layout.render(request, "load_mandates.html", {})
