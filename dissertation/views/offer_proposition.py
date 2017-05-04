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
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from base import models as mdl
from dissertation.models import adviser
from dissertation.models import faculty_adviser
from dissertation.models.offer_proposition import OfferProposition
from dissertation.models import offer_proposition
from dissertation.forms import ManagerOfferPropositionForm
from django.contrib.auth.decorators import user_passes_test
from base.views import layout


###########################
#      MANAGER VIEWS      #
###########################


@login_required
@user_passes_test(adviser.is_manager)
def manager_offer_parameters(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(adv)
    offer_props = offer_proposition.search_by_offer(offers)
    return layout.render(request, 'manager_offer_parameters.html', {'offer_propositions': offer_props})


@login_required
@user_passes_test(adviser.is_manager)
def manager_offer_parameters_edit(request, pk):
    offer_prop = get_object_or_404(OfferProposition, pk=pk)
    if request.method == "POST":
        form = ManagerOfferPropositionForm(request.POST, instance=offer_prop)
        if form.is_valid():
            form.save()
            return redirect('manager_offer_parameters')
    else:
        form = ManagerOfferPropositionForm(instance=offer_prop)
    return layout.render(request, "manager_offer_parameters_edit.html",
                         {'offer_proposition': offer_prop,
                          'form': form})
