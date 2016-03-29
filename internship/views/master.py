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
from internship.models import InternshipMaster

@login_required
def interships_masters(request):
    #First get the value of the 2 options for the sort
    if request.method == 'GET':
        speciality_sort_value = request.GET.get('speciality_sort')
        organization_sort_value = request.GET.get('organization_sort')

    #Then select Internship Master depending of the options
    #If both exist / if just speciality exist / if just organization exist / if none exist
    if speciality_sort_value and speciality_sort_value != "0":
        if organization_sort_value and organization_sort_value != "0":
            query = InternshipMaster.find_masters_by_speciality_and_organization(speciality_sort_value,
                                                                                organization_sort_value)
        else:
            query = InternshipMaster.find_masters_by_speciality(speciality_sort_value)
    else:
        if organization_sort_value and organization_sort_value != "0":
            query = InternshipMaster.find_masters_by_organization(organization_sort_value)
        else :
            query = InternshipMaster.find_masters()

    #Create the options for the selected list, delete dubblons
    query_master = InternshipMaster.find_masters()
    master_specs = []
    master_organizations = []
    for master in query_master:
        master_specs.append(master.speciality)
        master_organizations.append(master.organization)
    master_specs = list(set(master_specs))
    master_organizations = list(set(master_organizations))

    return render(request, "interships_masters.html", {'section': 'internship',
                                                        'all_masters': query, 'all_spec' : master_specs, 'all_organizations' : master_organizations,
                                                        'speciality_sort_value':speciality_sort_value, 'organization_sort_value':organization_sort_value})
