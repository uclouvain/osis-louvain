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
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from base import models as mdl
from dissertation.models.adviser import find_by_person
from dissertation.models.faculty_adviser import find_faculty_adviser_by_adviser
from dissertation.models.offer_proposition import OfferProposition
from dissertation.forms import ManagerOfferPropositionForm
from django.contrib.auth.decorators import user_passes_test
from base.views import layout


# Used by decorator @user_passes_test(is_manager) to secure manager views
def is_manager(user):
    person = mdl.person.find_by_user(user)
    adviser = find_by_person(person)
    return adviser.type == 'MGR'


@login_required
@user_passes_test(is_manager)
def manager_offer_parameters(request):
    person = mdl.person.find_by_user(request.user)
    adviser = find_by_person(person)
    faculty_adviser = find_faculty_adviser_by_adviser(adviser)
    offer_propositions = OfferProposition.objects.distinct().filter(offer=faculty_adviser).order_by('offer')
    return layout.render(request, 'manager_offer_parameters.html', {'offer_propositions': offer_propositions})


@login_required
@user_passes_test(is_manager)
def manager_offer_parameters_detail(request, pk):
    offer_proposition = get_object_or_404(OfferProposition, pk=pk)
    return layout.render(request, 'manager_offer_parameters_detail.html', {'offer_proposition': offer_proposition})


@login_required
@user_passes_test(is_manager)
def manager_offer_parameters_edit(request, pk):
    offer = get_object_or_404(OfferProposition, pk=pk)
    if request.method == "POST":
        form = ManagerOfferPropositionForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.save()
            return redirect('manager_offer_parameters')
    else:
        form = ManagerOfferPropositionForm(instance=offer)
    return layout.render(request, "manager_offer_parameters_edit.html", {'offer': offer, 'form': form})
