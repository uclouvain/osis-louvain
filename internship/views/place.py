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
from django.contrib.auth.decorators import login_required, permission_required
from internship.models import Organization, OrganizationAddress, InternshipChoice, InternshipOffer
from internship.forms import OrganizationForm


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_places(request):
    # First get the value of the option for the sort
    if request.method == 'GET':
        city_sort_get = request.GET.get('city_sort')

    # Second, import all the organizations with their address(es if they have more than one)
    organizations = Organization.find_by_type("service partner", order_by=['reference'])
    if organizations:
        for organization in organizations:
            organization.address = ""
            organization.student_choice = 0
            address = OrganizationAddress.find_by_organization(organization)
            if address:
                organization.address = address
            organization.student_choice = len(InternshipChoice.find_by(s_organization=organization))

    # Next, if there is a value for the sort, browse all the organizations and put which have the same city
    # in the address than the sort option
    l_organizations = []
    if city_sort_get and city_sort_get != "0":
        index = 0
        for orga in organizations:
            flag_del = 1
            if orga.address:
                for a in orga.address:
                    if a.city == city_sort_get:
                        flag_del = 0
                        break
            if flag_del == 0:
                l_organizations.append(orga)
            index += 1
    else:
        l_organizations = organizations

    # Create the options for the selected list, delete dubblons
    organization_addresses = []
    for orga in organizations:
        for a in orga.address:
            organization_addresses.append(a.city)
    organization_addresses = list(set(organization_addresses))
    organization_addresses.sort()

    return render(request, "places.html", {'section': 'internship',
                                           'all_organizations': l_organizations,
                                           'all_addresses': organization_addresses,
                                           'city_sort_get': city_sort_get})

@login_required
def internships_places_stud(request):
    # First get the value of the option for the sort
    if request.method == 'GET':
        city_sort_get = request.GET.get('city_sort')

    # Second, import all the organizations with their address(es if they have more than one)
    organizations = Organization.find_by_type("service partner", order_by=['reference'])
    if organizations:
        for organization in organizations:
            organization.address = ""
            organization.student_choice = 0
            address = OrganizationAddress.find_by_organization(organization)
            if address:
                organization.address = address
            organization.student_choice = len(InternshipChoice.find_by(s_organization=organization))

    # Next, if there is a value for the sort, browse all the organizations and put which have the same city
    # in the address than the sort option
    l_organizations = []
    if city_sort_get and city_sort_get != "0":
        index = 0
        for orga in organizations:
            flag_del = 1
            if orga.address:
                for a in orga.address:
                    if a.city == city_sort_get:
                        flag_del = 0
                        break
            if flag_del == 0:
                l_organizations.append(orga)
            index += 1
    else:
        l_organizations = organizations

    # Create the options for the selected list, delete dubblons
    organization_addresses = []
    for orga in organizations:
        for a in orga.address:
            organization_addresses.append(a.city)
    organization_addresses = list(set(organization_addresses))
    organization_addresses.sort()

    return render(request, "places_stud.html", {'section': 'internship',
                                           'all_organizations': l_organizations,
                                           'all_addresses': organization_addresses,
                                           'city_sort_get': city_sort_get})


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def place_save(request, organization_id, organization_address_id):
    print(organization_id)
    form = OrganizationForm(data=request.POST)
    if organization_id:
        organization = Organization.find_by_id(organization_id)
    else:
        organization = Organization()

    # get the screen modifications
    if request.POST['acronym']:
        organization.acronym = request.POST['acronym']
    else:
        organization.acronym = None

    if request.POST['name']:
        organization.name = request.POST['name']
    else:
        organization.name = None

    if request.POST['website']:
        organization.website = request.POST['website']
    else:
        organization.website = ""

    if request.POST['reference']:
        organization.reference = request.POST['reference']
    else:
        organization.reference = None

    organization.type = "service partner"

    organization.save()

    if organization_address_id:
        organization_address = OrganizationAddress.find_by_id(organization_address_id)
    else:
        organization_address = OrganizationAddress()

    organization_address.organization = organization
    if request.POST['organization_address_label']:
        organization_address.label = request.POST['organization_address_label']
    else:
        organization_address.label = None

    if request.POST['organization_address_location']:
        organization_address.location = request.POST['organization_address_location']
    else:
        organization_address.location = None

    if request.POST['organization_address_postal_code']:
        organization_address.postal_code = request.POST['organization_address_postal_code']
    else:
        organization_address.postal_code = None

    if request.POST['organization_address_city']:
        organization_address.city = request.POST['organization_address_city']
    else:
        organization_address.city = None

    if request.POST['organization_address_country']:
        organization_address.country = request.POST['organization_address_country']
    else:
        organization_address.country = None

    if request.POST['organization_id']:
        organization_address.organization = Organization.find_by_id(int(request.POST['organization_id']))

    organization_address.save()

    return render(request, "place_form.html", {'organization': organization,
                                                'organization_address':organization_address,
                                                'form': form,
                                                'message':"Hôpital correctement créé"
                                                })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def organization_new(request):
    return place_save(request, None, None)


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def organization_edit(request, organization_id):
    organization = Organization.find_by_id(organization_id)
    organization_address = OrganizationAddress.find_by_organization(organization)
    print(organization_address[0].id)
    return render(request, "place_form.html", {'organization':          organization,
                                               'organization_address':  organization_address[0], })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def organization_create(request):
    organization = Organization()
    return render(request, "place_form.html", {'organization': organization})


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_choice(request, reference):
    organization_choice = InternshipChoice.find_by(s_organization_ref=reference)
    organization = Organization.search(reference=reference)
    all_offers = InternshipOffer.find_interships_by_organization(organization[0])

    for al in all_offers:
        number_first_choice = len(InternshipChoice.find_by(s_organization=al.organization,
                                                           s_learning_unit_year=al.learning_unit_year,
                                                           s_choice=1))
        al.number_first_choice = number_first_choice

    return render(request, "place_detail.html", {'organization':        organization[0],
                                                 'organization_choice': organization_choice,
                                                 'offers':              all_offers, })
