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
from base import models as mdl
from pprint import pprint

@login_required
def internships_places(request):
    #First get the value of the option for the sort
    if request.method == 'GET':
        city_sort_get = request.GET.get('city_sort')

    #Second, import all the organizations with their address(es if they have more than one)
    organizations = mdl.organization.find_all_order_by_reference()
    if organizations:
        for organization in organizations:
            organization.address = ""
            address = mdl.organization_address.find_by_organization(organization)
            if address:
                organization.address = address

    #Next, if there is a value for the sort, browse all the organizations and put which have the same city
    #in the address than the sort option
    l_organizations=[]
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

    #Create the options for the selected list, delete dubblons
    organization_addresses = []
    for orga in organizations:
        for a in orga.address:
            organization_addresses.append(a.city)
    organization_addresses = list(set(organization_addresses))
    organization_addresses.sort()


    return render(request, "places.html", {'section': 'internship', 'all_organizations' : l_organizations, 'all_addresses' : organization_addresses,
                                            'city_sort_get':city_sort_get})
