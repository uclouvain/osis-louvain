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
from dissertation.models.adviser import Adviser, search_adviser
from dissertation.models import adviser
from dissertation.models import dissertation_role
from dissertation.models import faculty_adviser
from base import models as mdl
from dissertation.forms import AdviserForm, ManagerAdviserForm, ManagerAddAdviserForm, ManagerAddAdviserPreForm, \
    ManagerAddAdviserPerson, AddAdviserForm
from django.contrib.auth.decorators import user_passes_test
from base.views import layout
from base.models.enums import person_source_type


###########################
#      TEACHER VIEWS      #
###########################


@login_required
@user_passes_test(adviser.is_teacher)
def informations(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    return layout.render(request, "informations.html", {'adviser': adv,
                                                        'first_name': adv.person.first_name.title(),
                                                        'last_name': adv.person.last_name.title()
                                                        })


@login_required
@user_passes_test(adviser.is_teacher)
def informations_detail_stats(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)

    advisers_pro = dissertation_role.search_by_adviser_and_role_stats(adv, 'PROMOTEUR')
    count_advisers_pro = dissertation_role.count_by_adviser_and_role_stats(adv, 'PROMOTEUR')
    count_advisers_pro_request = dissertation_role.count_by_adviser(adv, 'PROMOTEUR', 'DIR_SUBMIT')
    tab_offer_count_pro = dissertation_role.get_tab_count_role_by_offer(advisers_pro)

    advisers_copro = dissertation_role.search_by_adviser_and_role_stats(adv, 'CO_PROMOTEUR')
    count_advisers_copro = dissertation_role.count_by_adviser_and_role_stats(adv, 'CO_PROMOTEUR')
    tab_offer_count_copro = dissertation_role.get_tab_count_role_by_offer(advisers_copro)

    advisers_reader = dissertation_role.search_by_adviser_and_role_stats(adv, 'READER')
    count_advisers_reader = dissertation_role.count_by_adviser_and_role_stats(adv, 'READER')
    tab_offer_count_read = dissertation_role.get_tab_count_role_by_offer(advisers_reader)

    return layout.render(request, 'informations_detail_stats.html',
                         {'adviser': adv,
                          'count_advisers_copro': count_advisers_copro,
                          'count_advisers_pro': count_advisers_pro,
                          'count_advisers_reader': count_advisers_reader,
                          'count_advisers_pro_request': count_advisers_pro_request,
                          'tab_offer_count_pro': tab_offer_count_pro,
                          'tab_offer_count_read': tab_offer_count_read,
                          'tab_offer_count_copro': tab_offer_count_copro})


@login_required
@user_passes_test(adviser.is_teacher)
def informations_edit(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    if request.method == "POST":
        form = AdviserForm(request.POST, instance=adv)
        if form.is_valid():
            adv = form.save(commit=False)
            adv.save()
            return redirect('informations')
    else:
        form = AdviserForm(instance=adv)
    return layout.render(request, "informations_edit.html", {'form': form,
                                                             'first_name': person.first_name.title(),
                                                             'last_name': person.last_name.title(),
                                                             'email': person.email,
                                                             'phone': person.phone,
                                                             'phone_mobile': person.phone_mobile})


@login_required
@user_passes_test(adviser.is_teacher)
def informations_add(request):
    if request.method == "POST":
        if 'search_form' in request.POST:  # step 2 : second form to select person in list
            form = ManagerAddAdviserPreForm(request.POST)
            if form.is_valid():  # mail format is valid
                data = form.cleaned_data
                person = mdl.person.search_by_email(data['email'])

                if not data['email']:  # empty search -> step 1
                    form = ManagerAddAdviserPreForm()
                    message = "empty_data"
                    return layout.render(request, 'informations_add_search.html', {'form': form,
                                                                                   'message': message})

                elif person and adviser.find_by_person(person):  # person already adviser -> step 1
                    form = ManagerAddAdviserPreForm()
                    email = "%s (%s)" % (list(person)[0], data['email'])
                    message = "person_already_adviser"
                    return layout.render(request, 'informations_add_search.html', {'form': form,
                                                                                   'message': message,
                                                                                   'email': email})
                elif mdl.person.count_by_email(data['email']) > 0:  # person found and not adviser -> go forward
                    pers = list(person)[0]
                    select_form = AddAdviserForm()
                    return layout.render(request, 'informations_add.html', {'form': select_form, 'pers': pers})

                else:  # person not found by email -> step 1
                    form = ManagerAddAdviserPreForm()
                    email = data['email']
                    message = "person_not_found_by_mail"
                    message_add = "add_new_person_explanation"
                    return layout.render(request, 'informations_add_search.html', {'form': form,
                                                                                   'message': message,
                                                                                   'email': email,
                                                                                   'message_add': message_add})
            else:  # invalid form (invalid format for email)
                form = ManagerAddAdviserPreForm()
                message = "invalid_data"
                return layout.render(request, 'informations_add_search.html', {'form': form,
                                                                               'message': message})

        else:  # step 3 : everything ok, register the person as adviser
            form = AddAdviserForm(request.POST)
            if form.is_valid():
                adv = form.save(commit=False)
                adv.save()
                return layout.render(request, 'informations_add.html', {'adv': adv})
            else:
                return redirect('dissertations')

    else:  # step 1 : initial form to search person by email
        form = ManagerAddAdviserPreForm()
        return layout.render(request, 'manager_informations_add_search.html', {'form': form})

###########################
#      MANAGER VIEWS      #
###########################


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations(request):
    advisers = adviser.list_teachers()
    return layout.render(request, 'manager_informations_list.html', {'advisers': advisers})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_add(request):
    if request.method == "POST":
        if 'search_form' in request.POST:  # step 2 : second form to select person in list
            form = ManagerAddAdviserPreForm(request.POST)
            if form.is_valid():  # mail format is valid
                data = form.cleaned_data
                person = mdl.person.search_by_email(data['email'])

                if not data['email']:  # empty search -> step 1
                    form = ManagerAddAdviserPreForm()
                    message = "empty_data"
                    return layout.render(request, 'manager_informations_add_search.html', {'form': form,
                                                                                           'message': message})

                elif person and adviser.find_by_person(person):  # person already adviser -> step 1
                    form = ManagerAddAdviserPreForm()
                    email = "%s (%s)" % (list(person)[0], data['email'])
                    message = "person_already_adviser"
                    return layout.render(request, 'manager_informations_add_search.html', {'form': form,
                                                                                           'message': message,
                                                                                           'email': email})
                elif mdl.person.count_by_email(data['email']) > 0:  # person found and not adviser -> go forward
                    pers = list(person)[0]
                    select_form = ManagerAddAdviserForm()
                    return layout.render(request, 'manager_informations_add.html', {'form': select_form, 'pers': pers})

                else:  # person not found by email -> step 1
                    form = ManagerAddAdviserPreForm()
                    email = data['email']
                    message = "person_not_found_by_mail"
                    message_add = "add_new_person_explanation"
                    return layout.render(request, 'manager_informations_add_search.html', {'form': form,
                                                                                           'message': message,
                                                                                           'email': email,
                                                                                           'message_add': message_add})
            else:  # invalid form (invalid format for email)
                form = ManagerAddAdviserPreForm()
                message = "invalid_data"
                return layout.render(request, 'manager_informations_add_search.html', {'form': form,
                                                                                       'message': message})

        else:  # step 3 : everything ok, register the person as adviser
            form = ManagerAddAdviserForm(request.POST)
            if form.is_valid():
                adv = form.save(commit=False)
                adv.save()
                return redirect('manager_informations_detail', pk=adv.pk)
            else:
                return redirect('manager_informations')

    else:  # step 1 : initial form to search person by email
        form = ManagerAddAdviserPreForm()
        return layout.render(request, 'manager_informations_add_search.html', {'form': form})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_add_person(request):
    if request.method == "POST":
        form = ManagerAddAdviserPerson(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data['email'] and data['last_name'] and data['first_name']:
                person = mdl.person.Person(email=data['email'],
                                           last_name=data['last_name'],
                                           first_name=data['first_name'],
                                           phone=data['phone'],
                                           phone_mobile=data['phone_mobile'],
                                           source=person_source_type.DISSERTATION)
                person.save()
                adv = adviser.add(person, 'PRF', False, False, False, '')
                return redirect('manager_informations_detail', pk=adv.pk)
            else:
                form = ManagerAddAdviserPerson()
                return layout.render(request, 'manager_information_add_person.html', {'form': form})
        else:
            form = ManagerAddAdviserPerson()
            return layout.render(request, 'manager_information_add_person.html', {'form': form})
    else:
        form = ManagerAddAdviserPerson()
        return layout.render(request, 'manager_information_add_person.html', {'form': form})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_detail(request, pk):
    adv = get_object_or_404(Adviser, pk=pk)
    return layout.render(request, 'manager_informations_detail.html',
                         {'adviser': adv,
                          'first_name': adv.person.first_name.title(),
                          'last_name': adv.person.last_name.title()})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_edit(request, pk):
    adv = get_object_or_404(Adviser, pk=pk)
    if request.method == "POST":
        form = ManagerAdviserForm(request.POST, instance=adv)
        if form.is_valid():
            adv = form.save(commit=False)
            adv.save()
            return redirect('manager_informations_detail', pk=adv.pk)
    else:
        form = ManagerAdviserForm(instance=adv)
    return layout.render(request, "manager_informations_edit.html",
                         {'adviser': adv,
                          'form': form,
                          'first_name': adv.person.first_name.title(),
                          'last_name': adv.person.last_name.title(),
                          'email': adv.person.email,
                          'phone': adv.person.phone,
                          'phone_mobile': adv.person.phone_mobile})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_search(request):
    advisers = search_adviser(terms=request.GET['search'])
    return layout.render(request, "manager_informations_list.html", {'advisers': advisers})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_list_request(request):
    person = mdl.person.find_by_user(request.user)
    adv = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(adv)
    advisers_need_request = dissertation_role.list_teachers_action_needed(offers)

    return layout.render(request, "manager_informations_list_request.html",
                         {'advisers_need_request': advisers_need_request})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_detail_list(request, pk):
    person = mdl.person.find_by_user(request.user)
    connected_adviser = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(connected_adviser)
    adv = get_object_or_404(Adviser, pk=pk)

    adv_list_disserts_pro = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'PROMOTEUR', offers)
    adv_list_disserts_copro = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'CO_PROMOTEUR', offers)
    adv_list_disserts_reader = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'READER', offers)
    adv_list_disserts_accompanist = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'ACCOMPANIST', offers)
    adv_list_disserts_internship = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'INTERNSHIP', offers)
    adv_list_disserts_president = dissertation_role.search_by_adviser_and_role_and_offers(adv, 'PRESIDENT', offers)

    return layout.render(request, "manager_informations_detail_list.html", locals())


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_detail_list_wait(request, pk):
    person = mdl.person.find_by_user(request.user)
    connected_adviser = adviser.search_by_person(person)
    offers = faculty_adviser.search_by_adviser(connected_adviser)
    adv = get_object_or_404(Adviser, pk=pk)
    disserts_role=dissertation_role.search_by_adviser_and_role_and_waiting(adv, offers)

    return layout.render(request, "manager_informations_detail_list_wait.html",
                         {'disserts_role': disserts_role,'adviser':adv})


@login_required
@user_passes_test(adviser.is_manager)
def manager_informations_detail_stats(request, pk):
    adv = get_object_or_404(Adviser, pk=pk)

    advisers_pro = dissertation_role.search_by_adviser_and_role_stats(adv, 'PROMOTEUR')
    count_advisers_pro = dissertation_role.count_by_adviser_and_role_stats(adv, 'PROMOTEUR')
    count_advisers_pro_request = dissertation_role.count_by_adviser(adv, 'PROMOTEUR', 'DIR_SUBMIT')
    tab_offer_count_pro = dissertation_role.get_tab_count_role_by_offer(advisers_pro)

    advisers_copro = dissertation_role.search_by_adviser_and_role_stats(adv, 'CO_PROMOTEUR')
    count_advisers_copro = dissertation_role.count_by_adviser_and_role_stats(adv, 'CO_PROMOTEUR')
    tab_offer_count_copro = dissertation_role.get_tab_count_role_by_offer(advisers_copro)

    advisers_reader = dissertation_role.search_by_adviser_and_role_stats(adv, 'READER')
    count_advisers_reader = dissertation_role.count_by_adviser_and_role_stats(adv, 'READER')
    tab_offer_count_read = dissertation_role.get_tab_count_role_by_offer(advisers_reader)

    return layout.render(request, 'manager_informations_detail_stats.html',
                         {'adviser': adv,
                          'count_advisers_copro': count_advisers_copro,
                          'count_advisers_pro': count_advisers_pro,
                          'count_advisers_reader': count_advisers_reader,
                          'count_advisers_pro_request': count_advisers_pro_request,
                          'tab_offer_count_pro': tab_offer_count_pro,
                          'tab_offer_count_read': tab_offer_count_read,
                          'tab_offer_count_copro': tab_offer_count_copro})
