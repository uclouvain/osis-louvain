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
from base import models as mdl
from internship.models import InternshipOffer, InternshipStudentInformation, OrganizationAddress, InternshipStudentAffectationStat

@login_required
@permission_required('internship.can_access_internship', raise_exception=True)
def internships_home(request):
    """
        The function of the home page :
        check if the user is a student and if internships are selectables.
        Also check if the students and organizations have their latitude/longitude,
        if not, compute it (function present in the OrganizationAddress' model)
    """
    student = mdl.student.find_by(person_username=request.user)
    #Check if the user is a student, if not the noma is not requiered so it's 0
    if len(student) > 0:
        for s in student:
            noma = s.registration_id
    else:
        noma = 0

    internships = InternshipOffer.find_internships()
    #Check if there is a internship offers in data base. If not, the internships
    #can be block, but there is no effect
    if len(internships) > 0:
        if internships[0].selectable:
            blockable = True
        else:
            blockable = False
    else:
        blockable = True

    affectations = InternshipStudentAffectationStat.search()
    # Check if there is an affectation in data base. If not, the affectations
    # aren't visible, if there is, it depend of the visible fields
    if len(affectations) > 0:
        if affectations[0].visible:
            affectation_visible = True
        else:
            affectation_visible = False
    else:
        affectation_visible = False

    #Find all informations about students and organisation and fin the latitude and longitude of the address
    student_informations = InternshipStudentInformation.search()
    organization_informations = OrganizationAddress.search()
    OrganizationAddress.find_latitude_longitude(student_informations)
    OrganizationAddress.find_latitude_longitude(organization_informations)

    return render(request, "internships_home.html", {'section': 'internship',
                                                     'noma': noma,
                                                     'blockable': blockable,
                                                     'affectation_visible': affectation_visible,
                                                     })
