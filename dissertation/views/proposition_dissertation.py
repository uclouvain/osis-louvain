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
from dissertation.models import adviser, dissertation, faculty_adviser, offer_proposition, proposition_dissertation,\
    proposition_document_file, proposition_offer, proposition_role
from dissertation.models.proposition_dissertation import PropositionDissertation
from dissertation.models.proposition_offer import PropositionOffer
from dissertation.models.proposition_role import PropositionRole
from dissertation.forms import PropositionDissertationForm, ManagerPropositionDissertationForm,\
    ManagerPropositionRoleForm, ManagerPropositionDissertationEditForm
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl import Workbook
from django.contrib.auth.decorators import user_passes_test
from base.views import layout
import time
from django.http import HttpResponse


def detect_in_request(request, wanted_key, wanted_value):
    for key in request.POST:
        if wanted_key in key and request.POST[key] == wanted_value:
            return True
    return False


def edit_proposition(form, proposition_offers, request):
    proposition = form.save()
    for old in proposition_offers:
        old.delete()
    generate_proposition_offers(request, proposition)
    return proposition


def create_proposition(form, person, request):
    proposition = form.save()
    proposition.set_creator(person)
    generate_proposition_offers(request, proposition)
    return proposition


def generate_proposition_offers(request, proposition):
    for key, value in request.POST.items():
        if 'txt_checkbox_' in key and value == 'on':
            offer = PropositionOffer()
            offer.proposition_dissertation = proposition
            offer_proposition_id = key.replace("txt_checkbox_", "")
            offer.offer_proposition = offer_proposition.find_by_id(int(offer_proposition_id))
            offer.save()


def is_valid(request, form):
    return form.is_valid() and detect_in_request(request, 'txt_checkbox_', 'on')


###########################
#      MANAGER VIEWS      #
###########################


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertations(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(adv)
    propositions_dissertations = proposition_dissertation.search_by_offers(offers)
    return layout.render(request, 'manager_proposition_dissertations_list.html',
                         {'propositions_dissertations': propositions_dissertations})


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertation_delete(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    proposition.deactivate()
    return redirect('manager_proposition_dissertations')


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertation_detail(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    offer_propositions = proposition_offer.find_by_proposition_dissertation(proposition)
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    count_use = dissertation.count_by_proposition(proposition)
    percent = count_use * 100 / proposition.max_number_student if proposition.max_number_student else 0
    count_proposition_role = proposition_role.count_by_proposition(proposition)
    files = proposition_document_file.find_by_proposition(proposition)
    filename = ""
    for file in files:
        filename = file.document_file.file_name
    if count_proposition_role < 1:
        proposition_role.add('PROMOTEUR', proposition.author, proposition)
    proposition_roles = proposition_role.search_by_proposition(proposition)
    return layout.render(request, 'manager_proposition_dissertation_detail.html',
                         {'proposition_dissertation': proposition,
                          'offer_propositions': offer_propositions,
                          'adviser': adv,
                          'count_use': count_use,
                          'percent': round(percent, 2),
                          'proposition_roles': proposition_roles,
                          'count_proposition_role': count_proposition_role,
                          'filename': filename})


@login_required
@user_passes_test(adviser.is_manager)
def manage_proposition_dissertation_edit(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    offer_propositions = offer_proposition.find_all_ordered_by_acronym()
    offer_propositions_error = None
    proposition_offers = proposition_offer.find_by_proposition_dissertation(proposition)
    if request.method == "POST":
        form = ManagerPropositionDissertationEditForm(request.POST, instance=proposition)
        if is_valid(request, form):
            proposition = edit_proposition(form, proposition_offers, request)
            return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)
        if not detect_in_request(request, 'txt_checkbox_', 'on'):
            offer_propositions_error = 'select_at_least_one_item'
            proposition_offers = None
    else:
        form = ManagerPropositionDissertationEditForm(instance=proposition)
    return layout.render(request, 'manager_proposition_dissertation_edit.html',
                         {'prop_dissert': proposition,
                          'form': form,
                          'author': proposition.author,
                          'types_choices': PropositionDissertation.TYPES_CHOICES,
                          'levels_choices': PropositionDissertation.LEVELS_CHOICES,
                          'collaborations_choices': PropositionDissertation.COLLABORATION_CHOICES,
                          'offer_propositions': offer_propositions,
                          'offer_propositions_error': offer_propositions_error,
                          'proposition_offers': proposition_offers})


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertations_jury_edit(request, pk):
    prop_role = get_object_or_404(PropositionRole, pk=pk)
    proposition = prop_role.proposition_dissertation
    return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertations_jury_new(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    count_proposition_role = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
    if request.method == "POST":
        form = ManagerPropositionRoleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            status = data['status']
            adv = data['adviser']
            prop = data['proposition_dissertation']
            if status == "PROMOTEUR":
                proposition.set_author(adv)
                proposition_role.delete(status, prop)
                proposition_role.add(status, adv, prop)
            elif count_proposition_role < 4:
                proposition_role.add(status, adv, prop)
            return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)
        else:
            form = ManagerPropositionRoleForm(initial={'proposition_dissertation': proposition})
    else:
        form = ManagerPropositionRoleForm(initial={'proposition_dissertation': proposition})
    return layout.render(request, 'manager_proposition_dissertations_jury_edit.html', {'form': form})


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertations_role_delete(request, pk):
    prop_role = get_object_or_404(PropositionRole, pk=pk)
    proposition = prop_role.proposition_dissertation
    prop_role.delete()
    return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertation_new(request):
    offer_propositions = offer_proposition.find_all_ordered_by_acronym()
    offer_propositions_error = None
    if request.method == "POST":
        form = ManagerPropositionDissertationForm(request.POST)
        if is_valid(request, form):
            person = mdl.person.find_by_user(request.user)
            proposition = create_proposition(form, person, request)
            return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)
        else:
            offer_propositions_error = 'select_at_least_one_item'
    else:
        form = ManagerPropositionDissertationForm(initial={'active': True})

    return layout.render(request, 'manager_proposition_dissertation_new.html',
                         {'form': form,
                          'types_choices': PropositionDissertation.TYPES_CHOICES,
                          'levels_choices': PropositionDissertation.LEVELS_CHOICES,
                          'collaborations_choices': PropositionDissertation.COLLABORATION_CHOICES,
                          'offer_propositions_error': offer_propositions_error,
                          'offer_propositions': offer_propositions})


@login_required
@user_passes_test(adviser.is_manager)
def manager_proposition_dissertations_search(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(adv)
    propositions_dissertations = proposition_dissertation.search(request.GET['search'], active=True, offers=offers)

    if 'bt_xlsx' in request.GET:
        filename = "EXPORT_propositions_{}.xlsx".format(time.strftime("%Y-%m-%d_%H:%M"))
        workbook = Workbook(encoding='utf-8')
        worksheet1 = workbook.active
        worksheet1.title = "proposition_dissertation"
        worksheet1.append(['Date_de_création', 'Teacher', 'Title',
                           'Type', 'Level', 'Collaboration', 'Max_number_student', 'Visibility',
                           'Active', 'Programme(s)', 'Description'])
        types_choices = dict(PropositionDissertation.TYPES_CHOICES)
        levels_choices = dict(PropositionDissertation.LEVELS_CHOICES)
        collaboration_choices = dict(PropositionDissertation.COLLABORATION_CHOICES)
        for proposition in propositions_dissertations:
            offers = ""
            for offer in proposition.propositionoffer_set.all():
                offers += "{} ".format(str(offer))
            worksheet1.append([proposition.created_date,
                               str(proposition.author),
                               proposition.title,
                               str(types_choices[proposition.type]),
                               str(levels_choices[proposition.level]),
                               str(collaboration_choices[proposition.collaboration]),
                               proposition.max_number_student,
                               proposition.visibility,
                               proposition.active,
                               offers,
                               proposition.description
                               ])
        response = HttpResponse(save_virtual_workbook(workbook), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
        return response

    else:
        return layout.render(request, "manager_proposition_dissertations_list.html",
                             {'propositions_dissertations': propositions_dissertations})

###########################
#      TEACHER VIEWS      #
###########################


def get_current_adviser(request):
    person = mdl.person.find_by_user(request.user)
    return adviser.search_by_person(person)


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations(request):
    propositions_dissertations = proposition_dissertation.get_all_for_teacher(get_current_adviser(request))
    return layout.render(request, 'proposition_dissertations_list.html',
                         {'propositions_dissertations': propositions_dissertations})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertation_delete(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    proposition.deactivate()
    return redirect('proposition_dissertations')


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertation_detail(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    offer_propositions = proposition_offer.find_by_proposition_dissertation(proposition)
    count_use = dissertation.count_by_proposition(proposition)
    percent = count_use * 100 / proposition.max_number_student if proposition.max_number_student else 0
    count_proposition_role = proposition_role.count_by_proposition(proposition)
    files = proposition_document_file.find_by_proposition(proposition)
    filename = ""
    for file in files:
        filename = file.document_file.file_name
    if count_proposition_role < 1:
        proposition_role.add('PROMOTEUR', proposition.author, proposition)
    proposition_roles = proposition_role.search_by_proposition(proposition)
    return layout.render(request, 'proposition_dissertation_detail.html',
                         {'proposition_dissertation': proposition,
                          'offer_propositions': offer_propositions,
                          'adviser': get_current_adviser(request),
                          'count_use': count_use,
                          'percent': round(percent, 2),
                          'proposition_roles': proposition_roles,
                          'count_proposition_role': count_proposition_role,
                          'filename': filename})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertation_edit(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    adv = get_current_adviser(request)
    offer_propositions = offer_proposition.find_all_ordered_by_acronym()
    offer_propositions_error = None
    proposition_offers = proposition_offer.find_by_proposition_dissertation(proposition)
    if proposition.author == adv or proposition.creator == adv.person:
        if request.method == "POST":
            form = PropositionDissertationForm(request.POST, instance=proposition)
            if is_valid(request, form):
                proposition = edit_proposition(form, proposition_offers, request)
                return redirect('proposition_dissertation_detail', pk=proposition.pk)
            if not detect_in_request(request, 'txt_checkbox_', 'on'):
                offer_propositions_error = 'select_at_least_one_item'
                proposition_offers = None

        form = PropositionDissertationForm(instance=proposition)
        return layout.render(request, 'proposition_dissertation_edit.html',
                             {'prop_dissert': proposition,
                              'form': form,
                              'types_choices': PropositionDissertation.TYPES_CHOICES,
                              'levels_choices': PropositionDissertation.LEVELS_CHOICES,
                              'collaborations_choices': PropositionDissertation.COLLABORATION_CHOICES,
                              'offer_propositions': offer_propositions,
                              'offer_propositions_error': offer_propositions_error,
                              'proposition_offers': proposition_offers})
    else:
        return redirect('proposition_dissertation_detail', pk=proposition.pk)


@login_required
@user_passes_test(adviser.is_teacher)
def my_dissertation_propositions(request):
    propositions_dissertations = proposition_dissertation.get_mine_for_teacher(get_current_adviser(request))
    return layout.render(request, 'proposition_dissertations_list_my.html',
                         {'propositions_dissertations': propositions_dissertations})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations_created(request):
    propositions_dissertations = proposition_dissertation.get_created_for_teacher(get_current_adviser(request))
    return layout.render(request, 'proposition_dissertations_list_created.html',
                         {'propositions_dissertations': propositions_dissertations})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertation_new(request):
    person = mdl.person.find_by_user(request.user)
    offer_propositions = offer_proposition.find_all_ordered_by_acronym()
    offer_propositions_error = None
    if request.method == "POST":
        form = PropositionDissertationForm(request.POST)
        if is_valid(request, form):
            proposition = create_proposition(form, person, request)
            return redirect('proposition_dissertation_detail', pk=proposition.pk)
        else:
            offer_propositions_error = 'select_at_least_one_item'
    else:
        form = PropositionDissertationForm(initial={'author': get_current_adviser(request), 'active': True})

    return layout.render(request, 'proposition_dissertation_new.html',
                         {'form': form,
                          'types_choices': PropositionDissertation.TYPES_CHOICES,
                          'levels_choices': PropositionDissertation.LEVELS_CHOICES,
                          'collaborations_choices': PropositionDissertation.COLLABORATION_CHOICES,
                          'offer_propositions_error': offer_propositions_error,
                          'offer_propositions': offer_propositions})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations_search(request):
    propositions_dissertations = proposition_dissertation.search(terms=request.GET['search'],
                                                                 active=True,
                                                                 visibility=True,
                                                                 connected_adviser=get_current_adviser(request))
    return layout.render(request, "proposition_dissertations_list.html",
                         {'propositions_dissertations': propositions_dissertations})


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations_jury_edit(request, pk):
    prop_role = get_object_or_404(PropositionRole, pk=pk)
    proposition = prop_role.proposition_dissertation
    return redirect('proposition_dissertation_detail', pk=proposition.pk)


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations_jury_new(request, pk):
    proposition = get_object_or_404(PropositionDissertation, pk=pk)
    count_proposition_role = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
    adv = get_current_adviser(request)
    if proposition.author == adv or proposition.creator == adv.person:
        if request.method == "POST":
            form = ManagerPropositionRoleForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                status = data['status']
                adv = data['adviser']
                prop = data['proposition_dissertation']
                if status == "PROMOTEUR":
                    proposition.set_author(adv)
                    proposition_role.delete(status, prop)
                    proposition_role.add(status, adv, prop)
                elif count_proposition_role < 4:
                    proposition_role.add(status, adv, prop)
                return redirect('proposition_dissertation_detail', pk=proposition.pk)
            else:
                form = ManagerPropositionRoleForm(initial={'proposition_dissertation': proposition})
        else:
            form = ManagerPropositionRoleForm(initial={'proposition_dissertation': proposition})
        return layout.render(request, 'proposition_dissertations_jury_edit.html', {'form': form})
    else:
        return redirect('proposition_dissertation_detail', pk=proposition.pk)


@login_required
@user_passes_test(adviser.is_teacher)
def proposition_dissertations_role_delete(request, pk):
    prop_role = get_object_or_404(PropositionRole, pk=pk)
    proposition = prop_role.proposition_dissertation
    adv = get_current_adviser(request)

    if prop_role.status != 'PROMOTEUR' and (proposition.author == adv or proposition.creator == adv.person):
        prop_role.delete()

    return redirect('proposition_dissertation_detail', pk=proposition.pk)
